from crew_config import crew, cfo_copilot, Task, Crew

task = Task(
    description="Synthesize all previous forecasts and profit simulations into a board-ready executive narrative. Include key insights, recommendations, and strategic guidance for leadership.",
    expected_output="A comprehensive executive summary suitable for board presentation, including performance highlights, forecasts, and strategic recommendations.",
    agent=cfo_copilot
)

task_crew = Crew(
    agents=[cfo_copilot],
    tasks=[task],
    llm=crew.llm,
    verbose=True
)

print("\n" + "="*50)
print("Running CFO Executive Summary...")
print("="*50 + "\n")
result = task_crew.kickoff()
print("\n" + "="*50)
print("RESULT:")
print("="*50)
print(result)

