# ISSUE: OpenAI-compatible provider path is incomplete — judge and reply are Anthropic-SDK-only, fallback requires the Responses API

Status: OPEN. Needed for our spark (vLLM) environment; upstream-PR candidate.
Found: 2026-07-05, meta-harness CEO-Bench campaign 1 (base a8d5ade).

## Observed

The config exposes `social_post_llm_provider` / `enterprise_llm_provider`
with three effective values: `bedrock`, `anthropic` (both via the Anthropic
SDK's `.messages.create`), and anything else falling through to an OpenAI
client. But the coverage is uneven:

1. **`judge_agent_social_post` and `generate_customer_reply_to_agent` have
   no OpenAI path at all** (`src/saas_bench/customer_llm.py` ~1036 and
   ~1160; both call `bedrock_client.messages.create` unconditionally). The
   call site passes `customer_simulator.social_post_client`
   (`simulation.py`, `_process_agent_social_posts`), and that property
   **raises ValueError for provider "openai"** (`customer_llm.py` ~197).
   Combined with the silent judge except-handler, a provider="openai" run
   quietly zeroes all agent-post effects.
2. **The OpenAI fallback uses the Responses API** (`client.responses.create`
   with `reasoning={"effort": ...}` / `output_text` — e.g. `customer_llm.py`
   ~529, `simulation.py` macro path ~4091), not `chat.completions`. Most
   OpenAI-compatible local servers (vLLM et al.) primarily serve
   `/v1/chat/completions`; Responses-API support is newer/partial. So even
   the paths that *have* an OpenAI branch may not work against a local
   OpenAI-compatible endpoint.
3. The OpenAI client is constructed bare (`OpenAI()`,
   `src/saas_bench/server_entry.py:177`), so `OPENAI_BASE_URL` /
   `OPENAI_API_KEY` env vars do steer it — the plumbing for local endpoints
   exists; only the call-site coverage is missing.

## Why it matters (our use case)

We want the environment LLMs served by local vLLM boxes
(`sparkone:30001` — Gemma-4-31B-it-FP8; `sparktwo:30001` — Qwen3.6-27B-FP8)
instead of Bedrock/Anthropic. The zero-code path is provider="anthropic" +
`ANTHROPIC_BASE_URL` pointed at a server that speaks Anthropic's
`/v1/messages`.

## Test results (2026-07-06, verified end-to-end with the Anthropic SDK)

Both vLLM boxes DO serve `/v1/messages` (vllm-0.1.dev17235+gf52870f26):
Anthropic-format responses with `content[0].text`, `usage.input_tokens/
output_tokens`, `stop_reason` — everything the benchmark call sites read.

- **Gemma/sparkone: works unmodified** with `Anthropic(base_url=...)`,
  system + temperature included. Zero-code path CONFIRMED for a single-box
  setup.
- **Qwen/sparktwo: thinking is on by default** — the first content block is
  `{"type": "thinking", ...}`, and the benchmark's `content[0].text`
  raises `AttributeError: 'ThinkingBlock' object has no attribute 'text'`
  (verified). It also spends the whole `max_tokens` budget thinking.
  Anthropic-style `thinking: {"type": "disabled"}` is silently ignored;
  the working toggle is
  `extra_body={"chat_template_kwargs": {"enable_thinking": false}}`
  (verified — clean text block). Using Qwen therefore requires a small
  patch at the `.messages.create` call sites (or server-side default).
- **Two-box split is blocked by config shape:** `_create_anthropic_client`
  builds ONE bare `Anthropic()` from env, shared by both the social and
  enterprise slots — there is no per-slot base_url. Splitting
  social→sparkone / enterprise→sparktwo needs per-slot
  `*_llm_base_url` config fields (small change, natural companion to this
  issue) or a routing proxy that dispatches on model name.

Cheapest viable first run: Gemma on sparkone for BOTH slots, pure
config+env, no code changes.

## Test results addendum (2026-07-06, Responses API + role strictness)

- **Both boxes also serve `/v1/responses`** (the OpenAI Responses API),
  including function tools (`function_call` output items verified) and
  Qwen reasoning as a proper `reasoning` output item. This WEAKENS observed
  point 2 above: the benchmark's `client.responses.create` fallback IS
  viable against these vLLM builds — completing the OpenAI branch (option
  (a) below) would not require rewriting call sites to `chat.completions`
  for vLLM specifically, though `chat.completions` remains the more
  portable choice for upstream.
- **vLLM 0.20.0 (sparktwo) validates message roles strictly**: it 400s on
  `developer`-role messages (Responses) and on `system`-role messages
  inside the `messages` array (`/v1/messages`). sparkone's newer dev build
  (`0.1.dev17235+gf52870f26.d20260603`) accepts both. This does NOT affect
  the benchmark's own env-LLM calls (they pass `system` as the top-level
  param, which both builds accept) — it bites agent CLIs pointed at the
  boxes (Claude Code, codex). Fix: align sparktwo's vLLM to sparkone's
  build, or front it with a role-normalizing proxy.

## Suggested direction (not researched further)

Either (a) complete the OpenAI branch: thread the OpenAI client into the
judge/reply functions and use `chat.completions` (most portable), or
(b) document that non-Anthropic providers require an Anthropic-compatible
`/v1/messages` endpoint. (a) benefits upstream users generally — it makes
the whole environment runnable against any OpenAI-compatible server.
