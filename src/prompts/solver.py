from langchain_core.prompts import ChatPromptTemplate

SOLVER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the final report writer for a multi-agent research system. Write a "
     "clear, well-organized, factual report. Only cite sources that were actually "
     "provided - never invent citations or URLs."),
    ("human",
     "Original question: {user_question}\n\n"
     "Research plan: {research_plan}\n\n"
     "Findings and evidence:\n{findings}\n\n"
     "Calculations performed (if any): {calculations}\n\n"
     "Critic feedback: {critique}\n\n"
     "Sources available (title / url):\n{sources}\n\n"
     "Write the final report with these sections:\n"
     "## Executive Summary\n## Detailed Analysis\n## Key Findings\n## Evidence\n"
     "## Comparison (only if multiple alternatives were researched)\n## Limitations\n"
     "## Sources\n\n"
     "In the Sources section, list ONLY the actual titles and URLs given above."),
])

QUERY_REWRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You turn a research plan into effective, non-redundant web search queries. "
     "Respond ONLY with the requested structured JSON."),
    ("human",
     "Research goal: {research_goal}\n"
     "Sub-questions: {sub_questions}\n\n"
     "Produce: queries: a list of 3-6 distinct, high-value search queries "
     "(avoid near-duplicates)."),
])
