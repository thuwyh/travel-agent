"""
Travel Assistant Agent — Interview Code

This agent uses a reasoning model (openai/gpt-oss-20b on Groq) with native
function calling. The model exposes its chain-of-thought in a `reasoning` field
and uses structured tool_calls for actions — a natural ReAct pattern.

The agent works for simple queries but has critical bugs that cause silent
failures in production. Your task: find the bugs, explain why they matter,
and fix them. See README.md for details.
"""

import json
import asyncio
from typing import Any, Dict, List

from tools import ALL_TOOLS, TOOL_REGISTRY
from llm import chat_completion, SessionUsage, DEFAULT_MODEL

SYSTEM_PROMPT = """\
You are TravelBot, a premium AI travel assistant powered by real-time data.
You help users plan trips by searching flights, hotels, weather, restaurants,
attractions, activities, car rentals, and more.

## Core Behavior

- You MUST use the available tools to look up real-time information. Never
  fabricate flight prices, hotel rates, weather forecasts, or availability.
- When you have enough information to answer the user, respond in plain text
  without calling any tools.
- Always verify information before presenting it. If a user asks about prices,
  search first — do not guess.

## Response Guidelines

- Be conversational but concise. Avoid unnecessary filler.
- When presenting multiple options (flights, hotels, etc.), use a clear table
  or numbered list format for easy comparison.
- Always include prices in USD unless the user requests another currency.
- For flights: mention airline, price, stops, duration, departure/arrival times.
- For hotels: mention name, star rating, price per night, key amenities, distance
  to city center, and cancellation policy.
- For weather: mention temperature (high/low), condition, and rain probability.
- For activities: note whether they are weather-dependent (indoor vs outdoor).
- For restaurants: mention cuisine, price level, average cost per person, and rating.

## Planning Trips

When a user asks you to plan a multi-day trip:
1. Search for flights first (outbound and return if round-trip).
2. Search for hotels at the destination for the specified dates.
3. Check the weather forecast for the travel dates.
4. Based on the weather, suggest appropriate activities:
   - Sunny/clear days → outdoor activities (parks, walking tours, sightseeing).
   - Rainy/stormy days → indoor activities (museums, cooking classes, shows).
5. If the user mentions a budget, calculate the total cost across all components
   and verify it stays within budget. If it exceeds the budget, suggest cheaper
   alternatives or explain the shortfall.
6. Present a day-by-day itinerary with a cost breakdown.

## Budget Calculations

- Flight prices are per person per leg (one-way). Round-trip = 2 legs.
- Hotel prices are per room per night.
- Activity prices are per person unless stated otherwise.
- Restaurant costs: use avg_cost_per_person × number of diners.
- Always show your arithmetic step by step when computing totals.

## Safety and Accuracy

- Never recommend booking without showing the user the full cost breakdown first.
- Always confirm before making any bookings or cancellations.
- If a tool returns an error, explain the issue to the user and suggest alternatives.
- Do not make up visa requirements or travel advisories — use the tools.
"""


class TravelAgent:

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.usage = SessionUsage()

    async def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        max_iterations = 10
        for i in range(max_iterations):
            response = await chat_completion(
                messages=self.messages,
                tools=ALL_TOOLS,
                usage=self.usage,
                model=self.model,
                label=f"step={i + 1}",
            )
            msg = response.choices[0].message

            # Print reasoning (the model's chain-of-thought)
            reasoning = getattr(msg, "reasoning", None)
            if reasoning:
                print(f"\n--- Step {i + 1} (Reasoning) ---")
                print(reasoning)

            # If the model produced text content (no tool calls), it's the final answer
            if msg.content and not msg.tool_calls:
                self.messages.append({"role": "assistant", "content": msg.content})
                print(f"\n--- Step {i + 1} (Answer) ---")
                print(msg.content[:200])
                print(f"\n{'=' * 60}")
                print(self.usage.summary())
                print(f"{'=' * 60}")
                return msg.content

            # Process tool calls
            if msg.tool_calls:
                # Add the assistant message (with tool_calls) to history
                self.messages.append(msg.model_dump())

                print(f"\n--- Step {i + 1} (Tool Calls) ---")
                # Execute the first tool call only
                tc = msg.tool_calls[0]
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments)
                print(f"  {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                func = TOOL_REGISTRY.get(func_name)
                if func:
                    result = await func(**func_args)
                    observation = json.dumps(result, ensure_ascii=False)
                else:
                    observation = json.dumps({"error": f"Unknown tool: {func_name}"})

                print(f"  -> {observation[:200]}")
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": observation,
                })
            else:
                # No content and no tool calls — shouldn't happen, but handle it
                self.messages.append({"role": "assistant", "content": msg.content or ""})
                self.messages.append({
                    "role": "user",
                    "content": "Please continue or provide your final answer.",
                })

        print(f"\n{'=' * 60}")
        print(self.usage.summary())
        print(f"{'=' * 60}")
        return "Sorry, I was unable to complete your request."


async def main():
    agent = TravelAgent()
    print("=== TravelBot (ReAct) ===")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        reply = await agent.chat(user_input)
        print(f"\nTravelBot: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())
