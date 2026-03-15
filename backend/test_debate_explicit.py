import asyncio
import os
import json
from dotenv import load_dotenv

from app.models.schemas import AgentOutput, AgentName, BrainConfig
from app.services.debate_engine import run_debate, compute_disagreement_score
from agents.groq_client import call_groq

load_dotenv()

async def main():
    print("\n--- FORCING DEBATE ENGINE TEST ---")
    
    # Create outputs that aggressively contradict each other to force a high disagreement score
    # We'll use low confidences specifically to trigger the "low confidence ratio" penalty
    outputs = [
        AgentOutput(
            agent=AgentName.ANALYTICAL,
            reasoning="The numbers clearly show the server architecture is fine. The issue is purely front-end caching. We shouldn't touch the backend.",
            response="Do absolutely nothing to the backend. It's a waste of time.",
            confidence=0.9
        ),
        AgentOutput(
            agent=AgentName.RED_TEAM,
            reasoning="The frontend caching is a symptom. The backend database queries are atrocious and causing the timeouts.",
            response="Rewrite the entire backend database layer immediately. It's fundamentally broken.",
            confidence=0.9
        ),
        AgentOutput(
            agent=AgentName.ETHICAL,
            reasoning="I'm not sure what the technical issue is, but we need to tell the users immediately that their data might be at risk.",
            response="Shut down the service and email all users. We don't know what's going on.",
            confidence=0.2
        )
    ]
    
    score = compute_disagreement_score(outputs)
    print(f"\nDisagreement Score (Calculated directly): {score}")
    print(f"Threshold for debate is 0.15. Will debate? {'YES' if score >= 0.15 else 'NO'}")
    
    if score >= 0.15:
        print("\nExecuting Debate Engine...")
        result = run_debate(
            outputs=outputs,
            user_query="The app is really slow today and I'm losing customers. What should we do?",
            call_groq_fn=call_groq
        )
        
        print(f"\nRounds executed: {result.get('rounds_executed')}")
        print(f"Final Disagreement Score: {result.get('disagreement_score')}")
        
        critiques = result.get('critiques', [])
        print(f"\nCritiques generated ({len(critiques)}):")
        for i, c in enumerate(critiques):
            print(f"  {i+1}. Target: {c.get('target_agent')}")
            print(f"     Text: {c.get('critique')}")
            
        print(f"\nSynthesis Suggestion:\n  {result.get('synthesis_suggestion')}")

if __name__ == "__main__":
    asyncio.run(main())
