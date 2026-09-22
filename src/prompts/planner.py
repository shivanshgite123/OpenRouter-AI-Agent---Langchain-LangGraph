from langchain_core.prompts import ChatPromptTemplate

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a meticulous research planner. Break the user's question into a "
     "clear research strategy. Respond ONLY with the requested structured JSON."),
    ("human",
     "User question:\n{user_question}\n\n"
     "Produce:\n"
     "1. research_goal: one sentence describing what a complete answer looks like\n"
     "2. sub_questions: 2-5 concrete sub-questions that must be answered\n"
     "3. required_sources: kinds of sources needed (news, official docs, papers, etc.)\n"
     "4. requires_research: true/false - does this need web research, or can it be "
     "answered from general knowledge/reasoning alone?"),
])
