import os
from dotenv import load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from oaitools import tools

load_dotenv()

# Initialize OpenAI
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.1
)

# SIMPLE PROMPT - tells agent exactly what to do
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a nutrition assistant. Follow these steps:

1. FIRST use detect_meal_type to check meal
2. If meal is unknown, ask user: "What meal was this? (breakfast/lunch/dinner/snack)"
3. If meal is known, then:
   - get_nutrition_data for the food
   - format_nutrition_facts to show details
   - save_meal_data to store it
   - generate_health_advice for tips

Always show the nutrition facts with calories, protein, carbs, fat, and fiber!"""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)

# Store conversations
user_conversations = {}

def ask_nutrition_agent(user_input: str, user_id: str = "default") -> str:
    """Main function that processes user messages"""
    try:
        # Get or create user conversation
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        # Process with agent
        result = executor.invoke({
            "input": user_input,
            "chat_history": user_conversations[user_id]
        })
        
        # Save conversation
        user_conversations[user_id].extend([
            HumanMessage(content=user_input),
            AIMessage(content=result["output"])
        ])
        
        return result["output"]
        
    except Exception as e:
        return f"Sorry, I encountered an error. Please try again! {str(e)}"

# Test function
if __name__ == "__main__":
    print("🥗 Nutrition Agent Started!")
    print("Try: '2 idli and sambar' or 'chicken sandwich for lunch'")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
            
        response = ask_nutrition_agent(user_input)
        print(f"\nBot: {response}")