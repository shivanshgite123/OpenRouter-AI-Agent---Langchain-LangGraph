from langchain_core.prompts import ChatPromptTemplate

RESEARCH_ANALYST_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a careful research analyst. Extract only facts that are directly "
     "supported by the provided documents. Never invent information or sources. "
     "Respond ONLY with the requested structured JSON."),
    ("human",
     "Research question: {user_question}\n"
     "Sub-questions: {sub_questions}\n\n"
     "Ranked documents (title / url / content):\n{documents}\n\n"
     "Produce a JSON object with:\n"
     "- findings: list of {{finding, evidence, source_url, source_title, confidence}}\n"
     "- missing_information: list of information still needed\n"
     "- agreements_and_conflicts: brief note on where sources agree/disagree"),
])

CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a rigorous, honest research critic performing a reflection step. "
     "You do NOT rewrite the answer - you evaluate whether the research so far is "
     "sufficient. Respond ONLY with the requested structured JSON."),
    ("human",
     "Original question: {user_question}\n"
     "Sub-questions: {sub_questions}\n"
     "Findings so far:\n{findings}\n"
     "Missing information noted by the analyst:\n{missing_information}\n\n"
     "Evaluate:\n"
     "- complete: true/false, is the question actually answerable now?\n"
     "- quality: one of ['sufficient', 'needs_more_research']\n"
     "- missing_information: list of what's still missing\n"
     "- follow_up_queries: concrete search queries that would fill the gaps\n"
     "- reason: one or two sentence justification"),
])

REPLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the replanning agent. Given critic feedback, decide the next "
     "concrete search queries to run. Avoid repeating queries that already ran. "
     "Respond ONLY with the requested structured JSON."),
    ("human",
     "Original question: {user_question}\n"
     "Previously run queries: {previous_queries}\n"
     "Critic's missing information: {missing_information}\n"
     "Critic's suggested follow-ups: {follow_up_queries}\n\n"
     "Produce: rewritten_queries: a list of 2-4 new, non-duplicate search queries."),
])
