# Amazon Connect -- GenAI Study Guide (AIP-C01)

Amazon Connect is a **minor exam topic** listed under "Customer Engagement" in the in-scope services. It will not be the focus of many questions, but it appears in scenarios involving AI-powered contact centers, agent assist, and customer self-service. Know it well enough to pick it as the right answer when the scenario is about a cloud contact center with GenAI capabilities.

---

## 1. Service Overview

Amazon Connect is a **fully managed, cloud-based contact center** service. It supports voice, chat, email, and task channels from a single platform. Agents interact with customers through a web-based Contact Control Panel (CCP).

### Core Components

| Component | Purpose |
|---|---|
| **Contact Flows** | Visual workflow builder that defines the customer experience (IVR menus, routing logic, bot handoffs, prompts) |
| **Queues** | Hold contacts waiting for an agent; routing profiles determine which queues an agent can handle |
| **Routing Profiles** | Map agents to queues with priority and delay settings |
| **Contact Control Panel (CCP)** | Web-based UI where agents handle interactions |
| **Customer Profiles** | Unified customer data from multiple sources |
| **Cases** | Track and manage customer issues across multiple contacts |

### Key Characteristic

Connect is **pay-per-use** with no upfront commitment, minimum fees, or long-term contracts. You pay per minute of voice usage and per message for chat.

---

## 2. GenAI Features

Amazon Connect's AI capabilities are **built on Amazon Bedrock**. Connect fully manages the underlying AI including model selection, prompt definition, and capacity provisioning. It may use **cross-region inference** to process requests optimally.

### Contact Lens (Analytics and Quality Management)

Contact Lens is the analytics engine built into Connect. It is powered by Bedrock and provides:

- **Conversational analytics** for voice, chat, and email -- sentiment analysis, issue detection, contact categorization
- **Real-time analytics** -- monitor live calls/chats for sentiment shifts, keyword triggers, compliance violations
- **Post-contact analytics** -- transcription, talk-time distribution, trend detection
- **Generative AI-powered post-contact summaries** -- auto-generated summaries of voice, chat, and email contacts so agents and supervisors do not need to read full transcripts
- **Semantic rule matching** -- categorize contacts using natural language statements (GenAI-powered) instead of rigid keyword lists
- **Sensitive data redaction** -- automatically redacts PII from transcripts, audio files, and emails
- **Automated agent performance evaluations** -- GenAI analyzes conversation transcripts to answer evaluation form questions, enabling managers to evaluate up to 100% of interactions

### Connect AI Agents (formerly Amazon Q in Connect)

Connect AI agents are the **real-time GenAI assistant** for both self-service and agent assist:

**For End Customers (Self-Service):**
- AI agents engage directly with customers over voice and chat
- Answer questions, take actions (process returns, update accounts), resolve issues autonomously
- Seamlessly escalate to human agents when needed, preserving full conversation context

**For Human Agents (Agent Assist):**
- Detect customer intent in real-time during calls, chats, tasks, and emails
- Provide generative responses, suggested actions, and links to relevant knowledge articles
- Agents can query the AI agent directly using natural language
- Auto-generate case summaries and email responses

**Customization:**
- Custom AI prompts and AI guardrails
- Integration with step-by-step guides
- Multiple knowledge bases per AI agent (including Amazon Bedrock Knowledge Bases)
- Supports Model Context Protocol (MCP) for accessing organizational resources
- GDPR compliant and HIPAA eligible

### Generative AI Email Support

- Auto-generates email conversation overviews, suggested actions, and draft responses
- Uses knowledge bases and custom prompts to tailor outputs

---

## 3. Integration with Bedrock and Lex

### Amazon Bedrock

- Connect's AI features (Contact Lens, AI agents, summaries, evaluations) all use models via **Amazon Bedrock**
- Connect manages model selection -- you do not choose which FM to use for built-in features
- Data protection: prompts and responses are never stored, logged, or shared by Bedrock, and are never used to train models
- Supports multiple Amazon Bedrock Knowledge Bases per AI agent, including existing Bedrock KBs without data duplication

### Amazon Lex

Amazon Lex provides the **traditional conversational AI** (intent-based chatbot) layer in Connect:

- Added to contact flows via the **"Get customer input" block**
- Handles structured interactions: DTMF input ("press 1 for..."), slot-filling ("what is your account number?"), intent detection
- Routes contacts to different flow branches based on detected intents
- Lex bots can be built directly in the Connect admin website

### Lex + Connect AI Agents (Complementary, Not Competing)

This is an important distinction for the exam:

| Capability | Amazon Lex | Connect AI Agents |
|---|---|---|
| **Approach** | Intent-based, rule-driven | Generative, context-aware |
| **Best for** | Predefined workflows, slot collection, DTMF menus | Open-ended questions, knowledge retrieval, dynamic actions |
| **Conversation style** | Structured (intents + slots) | Free-form natural language |
| **Underlying tech** | NLU/NLP models | LLMs via Bedrock |

They are designed to work together: Lex handles well-defined intents and structured data collection, while Connect AI agents handle open-ended queries and generative responses. A single contact flow can use both.

---

## 4. Exam Relevance

### When Connect Is the Answer

- Scenario describes a **cloud contact center** needing AI-powered agent assistance
- Question mentions **real-time agent coaching** or **post-contact summarization** for voice/chat
- Scenario involves **automated quality evaluation** of customer-agent conversations
- Question asks about **AI-powered self-service** over voice or chat in a contact center context
- Scenario requires **sentiment analysis on live customer calls**
- Question mentions **omnichannel** (voice + chat + email) customer engagement with AI

### When Connect Is NOT the Answer

| Scenario | Correct Service |
|---|---|
| Building a standalone chatbot (no contact center) | **Amazon Lex** (or Bedrock Agents) |
| General-purpose RAG application | **Amazon Bedrock Knowledge Bases** |
| Custom ML model for customer analytics | **Amazon SageMaker AI** |
| Email marketing campaigns | **Amazon SES** or **Amazon Pinpoint** |
| Push notifications or SMS campaigns | **Amazon Pinpoint** |
| Custom GenAI app with full model control | **Amazon Bedrock** directly |

### Key Differentiator

Connect is the answer when the question is specifically about a **contact center** use case. If the scenario does not mention agents handling calls/chats or a contact center, Connect is likely not the answer.

---

## 5. Exam Gotchas

1. **Contact Lens vs. Amazon Comprehend**: Contact Lens handles sentiment analysis *within Connect*. If the question is about sentiment analysis on arbitrary text outside a contact center, the answer is Amazon Comprehend. Inside a contact center scenario, it is Contact Lens.

2. **Connect AI Agents vs. Bedrock Agents**: Connect AI agents are purpose-built for the contact center (agent assist, self-service over phone/chat). Bedrock Agents are for general-purpose agentic workflows. If the scenario is a contact center, Connect AI agents is the answer.

3. **Lex alone vs. Lex in Connect**: Lex can be used independently for chatbots. When Lex appears in a Connect question, it is specifically the front-end IVR/chatbot component of the contact center flow. The exam may test whether you know Lex is added via the "Get customer input" flow block.

4. **Connect manages its own AI**: You do not pick a specific Bedrock model for Contact Lens or AI agents. Connect handles model selection, prompt engineering, and capacity internally. This is different from using Bedrock directly where you choose the model.

5. **Cross-region inference**: Connect may process AI inference requests in a different region than your Connect instance for optimal performance. All data stays encrypted on Amazon's network (never public internet). This may appear as a distractor about data residency.

6. **Post-contact summaries require Contact Lens enabled**: Generative AI summaries are a Contact Lens feature, not a standalone capability. The "Set recording and analytics behavior" flow block must be configured.

---

## 6. When to Use / When NOT to Use

### Use Amazon Connect When

- You need a **cloud-based contact center** with built-in AI capabilities
- You want **GenAI-powered agent assist** (real-time suggestions, auto-summaries, knowledge retrieval) in a call/chat center
- You need **automated quality management** with AI-evaluated agent performance
- You want **AI self-service** that can handle customer issues autonomously over voice and chat, with human escalation
- You need **omnichannel routing** (voice, chat, email, tasks) with AI analytics across all channels

### Do NOT Use Amazon Connect When

- You do not need a full contact center -- just a chatbot (use Lex or Bedrock Agents)
- You need general-purpose GenAI application development (use Bedrock directly)
- You need custom ML models for customer analytics (use SageMaker AI)
- You need marketing campaign management (use Pinpoint)
- You need only speech-to-text transcription without a contact center (use Amazon Transcribe)

---

## 7. Key Concepts Quick Reference

| Concept | Definition |
|---|---|
| **Contact Flow** | Defines the end-to-end customer experience: IVR menus, prompts, Lex bot handoffs, routing, AI agent integration |
| **Queue** | Where contacts wait to be routed to an available agent |
| **Routing Profile** | Determines which queues an agent handles and at what priority |
| **Contact Lens** | Built-in analytics: transcription, sentiment, categorization, summaries, evaluations |
| **Connect AI Agents** | GenAI assistant for both self-service and agent assist, powered by Bedrock |
| **Amazon Q in Connect** | Previous name for Connect AI agents (may still appear in exam materials) |
| **Get Customer Input block** | Flow block that invokes Amazon Lex bots for structured input collection |
| **Connect Assistant block** | Flow block that activates Connect AI agents for GenAI capabilities |
| **Post-Contact Summary** | GenAI-generated summary of a completed interaction (voice, chat, or email) |
| **Semantic Rule Matching** | GenAI-powered contact categorization using natural language instead of keyword lists |
| **Customer Profiles** | Unified customer data that AI agents use for personalized responses |
| **Cases** | Track customer issues across multiple contacts; AI can auto-summarize case history |

---

## 8. Architecture Patterns for Exam

### Pattern 1: AI-Powered IVR with Escalation
```
Customer Call -> Contact Flow -> Lex Bot (intent detection, slot filling)
  -> Resolved? -> End
  -> Not Resolved? -> Queue -> Human Agent (with Connect AI agent assist)
```

### Pattern 2: GenAI Self-Service with Human Fallback
```
Customer Chat -> Contact Flow -> Connect AI Agent (autonomous resolution)
  -> Resolved? -> End
  -> Complex Issue? -> Escalate to Human Agent (full context preserved)
```

### Pattern 3: Quality Management Loop
```
Contact Completed -> Contact Lens (transcription, sentiment, categorization)
  -> GenAI Post-Contact Summary
  -> Automated Performance Evaluation (GenAI answers evaluation criteria)
  -> Supervisor Review
```

---

## Summary for Exam Day

- Amazon Connect = **cloud contact center** with built-in GenAI
- All AI features run on **Amazon Bedrock** (managed by Connect, you do not pick the model)
- **Contact Lens** = analytics, sentiment, transcription, summaries, evaluations
- **Connect AI Agents** = real-time agent assist + customer self-service
- **Amazon Lex** = structured chatbot/IVR within Connect flows (complementary to AI agents)
- Pick Connect when the scenario is about a **contact center**; pick other services when it is not
- Connect AI agents are different from Bedrock Agents: Connect AI agents are purpose-built for contact center use cases
