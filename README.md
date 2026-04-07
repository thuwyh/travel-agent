# AI Agent Engineering Interview

## Overview

You'll work with a travel assistant agent built on `openai/gpt-oss-20b` (a
reasoning model hosted on Groq) using **native function calling**. The agent
has 44 tools covering flights, hotels, weather, restaurants, attractions,
activities, trains, insurance, events, and more.

The interview has three parts. You may use AI coding tools throughout.

## Setup

```bash
pip install -r requirements.txt
# .env with GROQ_API_KEY is provided
python agent.py
```

Try a simple query: `What's the weather in London?`

Then try something that requires multiple tool calls:
`Search flights from NYC to London on July 15, then check the weather there.`

## Part 1: Debug (30 min)

The agent works for trivial single-tool queries, but **crashes on anything
requiring multiple steps**. Find the bugs in `agent.py` and fix them.

For each bug, be prepared to explain:
- What goes wrong and why
- How you found it
- Why your fix is correct

## Part 2: Write Evaluations (20 min)

After fixing the bugs, write a test suite that verifies the agent works
correctly. Design test cases that cover:

- A simple single-tool query
- A complex multi-step query (e.g. flights + hotel + budget math)
- A multi-turn conversation where the second message references the first

For each test, decide: can you check the answer with **deterministic rules**
(keyword matching, regex, exact values from mock data), or do you need an
**LLM-as-judge**? Use the right approach for each.

The mock data in `tools.py` is deterministic — use that to your advantage.

## Part 3: Optimize Token Cost (20 min)

Look at the `[tokens]` log printed by every run. You'll see that each API
call sends all 44 tool definitions (~6,000 tokens) even when the query only
needs 3-4 tools.

Example from a simple 3-step session:
```
[tokens] step=1  prompt=4038  completion=130
[tokens] step=2  prompt=4619  completion=80
[tokens] step=3  prompt=5011  completion=829
SESSION TOTAL: prompt=13,668  cost=$0.000977
```

Reduce the per-session token cost. Measure before and after. Be prepared to
discuss the tradeoffs of your approach.

### Pricing reference

| Token type | Price per 1M tokens |
|-----------|-------------------|
| Input | $0.075 |
| Cached input | $0.037 |
| Output | $0.30 |

## Files

```
agent.py    ← Agent code — debug and optimize this
llm.py      ← LLM client wrapper with SessionUsage tracking
tools.py    ← 44 tool definitions + mock implementations
.env        ← API key (provided)
```

`llm.py` and `tools.py` are provided infrastructure — read them to understand
the setup, but you shouldn't need to modify them.
