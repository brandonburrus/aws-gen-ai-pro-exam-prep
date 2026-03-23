"""
Generate a PDF documenting Amazon Bedrock non-legacy foundation models.
Data sourced from AWS documentation (docs.aws.amazon.com/bedrock).
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime


PROVIDERS = [
    {
        "name": "AI21 Labs",
        "description": "AI21 Labs builds enterprise-grade language models based on a hybrid SSM-Transformer architecture (Mamba + Attention), enabling efficient processing of very long contexts.",
        "models": [
            {
                "model": "Jamba 1.5 Large",
                "model_id": "ai21.jamba-1-5-large-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex reasoning across long documents, summarization, analysis of large datasets",
                "strengths": "398B total params, 256K context window, hybrid SSM-Transformer architecture for efficient long-context processing",
            },
            {
                "model": "Jamba 1.5 Mini",
                "model_id": "ai21.jamba-1-5-mini-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Low-latency enterprise tasks, chat, Q&A, classification",
                "strengths": "52B total params, 256K context window, lightweight hybrid SSM-Transformer optimized for speed",
            },
        ],
    },
    {
        "name": "Amazon",
        "description": "Amazon's first-party foundation models span text, image, video, speech, and embeddings under the Nova and Titan families.",
        "models": [
            {
                "model": "Nova 2 Lite",
                "model_id": "amazon.nova-2-lite-v1:0",
                "input": "Text, Image, Video",
                "output": "Text",
                "use_cases": "Simple automation, document processing, customer support",
                "strengths": "Cost-efficient multimodal model, broad regional availability via cross-region inference",
            },
            {
                "model": "Nova 2 Sonic",
                "model_id": "amazon.nova-2-sonic-v1:0",
                "input": "Speech",
                "output": "Speech, Text",
                "use_cases": "Real-time voice conversations, voice assistants, telephony bots",
                "strengths": "Speech-to-speech foundation model, natural real-time voice with low latency",
            },
            {
                "model": "Nova Micro",
                "model_id": "amazon.nova-micro-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Summarization, translation, classification, brainstorming",
                "strengths": "Fastest Amazon text-only model, optimized for speed and low cost",
            },
            {
                "model": "Nova Lite",
                "model_id": "amazon.nova-lite-v1:0",
                "input": "Text, Image, Video",
                "output": "Text",
                "use_cases": "Document analysis, visual Q&A, video understanding",
                "strengths": "Low-cost multimodal model processing text, images, and video inputs",
            },
            {
                "model": "Nova Pro",
                "model_id": "amazon.nova-pro-v1:0",
                "input": "Text, Image, Video",
                "output": "Text",
                "use_cases": "Broad range of tasks: analysis, coding, content creation, agents",
                "strengths": "Best balance of accuracy, speed, and cost among Nova models",
            },
            {
                "model": "Nova Premier",
                "model_id": "amazon.nova-premier-v1:0",
                "input": "Text, Image, Video",
                "output": "Text",
                "use_cases": "Complex reasoning, agentic workflows, model distillation",
                "strengths": "Highest-capability Amazon multimodal model for demanding tasks",
            },
            {
                "model": "Nova Canvas",
                "model_id": "amazon.nova-canvas-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Text-to-image generation, image editing, creative design",
                "strengths": "Studio-quality images with built-in watermarking and content moderation controls",
            },
            {
                "model": "Nova Reel",
                "model_id": "amazon.nova-reel-v1:0",
                "input": "Text, Image",
                "output": "Video",
                "use_cases": "Short video generation, marketing content, motion graphics",
                "strengths": "Video generation from text/image prompts with camera motion controls",
            },
            {
                "model": "Nova Sonic",
                "model_id": "amazon.nova-sonic-v1:0",
                "input": "Speech",
                "output": "Speech, Text",
                "use_cases": "Real-time voice conversations, multilingual voice apps",
                "strengths": "Low-latency speech-to-speech model with multi-language support",
            },
            {
                "model": "Nova Multimodal Embeddings",
                "model_id": "amazon.nova-2-multimodal-embeddings-v1:0",
                "input": "Text, Image, Audio, Video",
                "output": "Embedding",
                "use_cases": "Multimodal search and retrieval across text, image, audio, video",
                "strengths": "Unified embedding model for all major modalities",
            },
            {
                "model": "Rerank 1.0",
                "model_id": "amazon.rerank-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Re-ranking search results in RAG pipelines",
                "strengths": "Purpose-built for improving search result relevance",
            },
            {
                "model": "Titan Text Embeddings V2",
                "model_id": "amazon.titan-embed-text-v2:0",
                "input": "Text",
                "output": "Embedding",
                "use_cases": "Semantic search, retrieval, text classification, clustering",
                "strengths": "Configurable output dimensions, improved accuracy, 100+ languages, wide regional availability",
            },
            {
                "model": "Titan Multimodal Embeddings G1",
                "model_id": "amazon.titan-embed-image-v1",
                "input": "Text, Image",
                "output": "Embedding",
                "use_cases": "Multimodal search, recommendation, personalization",
                "strengths": "Generates embeddings from both text and images for cross-modal retrieval",
            },
            {
                "model": "Titan Embeddings G1 - Text",
                "model_id": "amazon.titan-embed-text-v1",
                "input": "Text",
                "output": "Embedding",
                "use_cases": "Text retrieval, semantic similarity, clustering",
                "strengths": "Converts text to vector representations for search and personalization",
            },
            {
                "model": "Titan Image Generator G1 v2",
                "model_id": "amazon.titan-image-generator-v2:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Text-to-image generation, image editing, image variations",
                "strengths": "Photorealistic images with subject consistency, background removal, built-in watermarking",
            },
            {
                "model": "Titan Text Large",
                "model_id": "amazon.titan-tg1-large",
                "input": "Text",
                "output": "Text",
                "use_cases": "Summarization, text generation, conversational chat",
                "strengths": "General-purpose text generation with broad use-case coverage",
            },
        ],
    },
    {
        "name": "Anthropic",
        "description": "Anthropic builds the Claude family of models, known for strong reasoning, coding, and safety. Claude models on Bedrock range from the fast Haiku tier to the flagship Opus tier.",
        "models": [
            {
                "model": "Claude Opus 4.6",
                "model_id": "anthropic.claude-opus-4-6-v1",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Complex agentic tasks, massive codebase operations, long-running autonomous work",
                "strengths": "Flagship model; plans more carefully, sustains agentic tasks longer, reliable in massive codebases",
            },
            {
                "model": "Claude Opus 4.5",
                "model_id": "anthropic.claude-opus-4-5-20251101-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Coding, agents, computer use, spreadsheets, long-running chats",
                "strengths": "Strong coding and agent performance with improvements for spreadsheets and extended conversations",
            },
            {
                "model": "Claude Opus 4.1",
                "model_id": "anthropic.claude-opus-4-1-20250805-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Coding, reasoning, agentic tasks, complex analysis",
                "strengths": "Improved coding, reasoning, and agentic capabilities over Opus 4.0",
            },
            {
                "model": "Claude Sonnet 4.6",
                "model_id": "anthropic.claude-sonnet-4-6",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Coding, computer use, long-context reasoning, agent planning",
                "strengths": "Full upgrade of mid-tier model; improved coding, computer use, 1M token context window",
            },
            {
                "model": "Claude Sonnet 4.5",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Agents, coding, computer use, general reasoning",
                "strengths": "Significant improvements across all benchmarks, optimized for agent and coding workflows",
            },
            {
                "model": "Claude Sonnet 4",
                "model_id": "anthropic.claude-sonnet-4-20250514-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Coding, reasoning, instruction following, tool use",
                "strengths": "Balanced model with extended thinking and tool use, strong instruction following",
            },
            {
                "model": "Claude Haiku 4.5",
                "model_id": "anthropic.claude-haiku-4-5-20251001-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Fast classification, lightweight agents, quick coding tasks",
                "strengths": "Lightweight, optimized for speed and efficiency with strong coding/agent performance",
            },
            {
                "model": "Claude 3.5 Haiku",
                "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Fast responses, coding, classification, chat",
                "strengths": "Improved coding and reasoning over Claude 3 Haiku at the same speed tier",
            },
            {
                "model": "Claude 3 Haiku",
                "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Near-instant responses, chat, lightweight tasks",
                "strengths": "Fastest, most compact Claude 3 model; optimized for speed and efficiency",
            },
        ],
    },
    {
        "name": "Cohere",
        "description": "Cohere specializes in enterprise search, RAG, and embeddings. Their models are purpose-built for retrieval, reranking, and multilingual understanding.",
        "models": [
            {
                "model": "Command R+",
                "model_id": "cohere.command-r-plus-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex RAG workflows, multi-step tool use, enterprise tasks",
                "strengths": "128K context window, optimized for sophisticated retrieval-augmented generation",
            },
            {
                "model": "Command R",
                "model_id": "cohere.command-r-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "RAG, tool use, enterprise applications",
                "strengths": "Scalable LLM optimized for retrieval-augmented generation, 128K context",
            },
            {
                "model": "Embed v4",
                "model_id": "cohere.embed-v4:0",
                "input": "Text, Image",
                "output": "Embedding",
                "use_cases": "Multimodal search, RAG, mixed text/image retrieval",
                "strengths": "Unified multimodal embedding model for text, images, and mixed content in a single model",
            },
            {
                "model": "Embed English",
                "model_id": "cohere.embed-english-v3",
                "input": "Text",
                "output": "Embedding",
                "use_cases": "English-language search, classification, clustering",
                "strengths": "Strong retrieval accuracy for English text embeddings",
            },
            {
                "model": "Embed Multilingual",
                "model_id": "cohere.embed-multilingual-v3",
                "input": "Text",
                "output": "Embedding",
                "use_cases": "Cross-lingual search, multilingual classification and clustering",
                "strengths": "Supports 100+ languages for cross-lingual retrieval",
            },
            {
                "model": "Rerank 3.5",
                "model_id": "cohere.rerank-v3-5:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Re-ranking search results in RAG pipelines, enterprise search",
                "strengths": "Purpose-built relevance scoring model for improved search accuracy",
            },
        ],
    },
    {
        "name": "DeepSeek",
        "description": "DeepSeek builds open-weight mixture-of-experts models with strong reasoning, coding, and math capabilities.",
        "models": [
            {
                "model": "DeepSeek V3.2",
                "model_id": "deepseek.v3.2",
                "input": "Text",
                "output": "Text",
                "use_cases": "General reasoning, coding, instruction following",
                "strengths": "Latest MoE model with improved reasoning, coding, and instruction following",
            },
            {
                "model": "DeepSeek-V3.1",
                "model_id": "deepseek.v3-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Coding, math, general reasoning",
                "strengths": "685B parameter MoE model with strong cross-domain performance",
            },
            {
                "model": "DeepSeek-R1",
                "model_id": "deepseek.r1-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex math, coding, logic problems requiring step-by-step reasoning",
                "strengths": "Chain-of-thought reasoning model purpose-built for hard problems",
            },
        ],
    },
    {
        "name": "Google",
        "description": "Google's Gemma 3 family of open models with instruction tuning, available in multiple sizes for different deployment targets.",
        "models": [
            {
                "model": "Gemma 3 27B PT",
                "model_id": "google.gemma-3-27b-it",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Visual reasoning, document understanding, general text tasks",
                "strengths": "Largest Gemma 3 model (27B params), multimodal, 128K context window",
            },
            {
                "model": "Gemma 3 12B IT",
                "model_id": "google.gemma-3-12b-it",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Text and image understanding, Q&A, classification",
                "strengths": "12B param open model with instruction tuning and 128K context",
            },
            {
                "model": "Gemma 3 4B IT",
                "model_id": "google.gemma-3-4b-it",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "On-device / edge deployment, lightweight text/image tasks",
                "strengths": "Compact 4B params, instruction-tuned, designed for edge deployment",
            },
        ],
    },
    {
        "name": "Luma AI",
        "description": "Luma AI specializes in video generation, producing high-quality video content from text prompts.",
        "models": [
            {
                "model": "Ray v2",
                "model_id": "luma.ray-v2:0",
                "input": "Text",
                "output": "Video",
                "use_cases": "Text-to-video generation, creative content, marketing videos",
                "strengths": "High-quality video generation from text prompts",
            },
        ],
    },
    {
        "name": "Meta",
        "description": "Meta's Llama family of open models spans from compact edge models (1B) to massive frontier models (405B), including multimodal and MoE variants.",
        "models": [
            {
                "model": "Llama 4 Maverick 17B",
                "model_id": "meta.llama4-maverick-17b-instruct-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Multimodal chat, instruction following, visual Q&A",
                "strengths": "17B active params, 128 experts MoE architecture, multimodal",
            },
            {
                "model": "Llama 4 Scout 17B",
                "model_id": "meta.llama4-scout-17b-instruct-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Long-document analysis, multimodal tasks, research",
                "strengths": "17B active params, 16 experts MoE, 10M token context window",
            },
            {
                "model": "Llama 3.3 70B Instruct",
                "model_id": "meta.llama3-3-70b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Reasoning, coding, general-purpose chat",
                "strengths": "70B params, improved efficiency, 128K context window",
            },
            {
                "model": "Llama 3.2 90B Instruct",
                "model_id": "meta.llama3-2-90b-instruct-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Visual reasoning, document understanding, image Q&A",
                "strengths": "90B params, multimodal (text + image), 128K context",
            },
            {
                "model": "Llama 3.2 11B Instruct",
                "model_id": "meta.llama3-2-11b-instruct-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Multimodal chat, image understanding, compact deployment",
                "strengths": "11B param multimodal model, 128K context window",
            },
            {
                "model": "Llama 3.2 3B Instruct",
                "model_id": "meta.llama3-2-3b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "On-device summarization, instruction following, edge tasks",
                "strengths": "Lightweight 3B model designed for on-device tasks",
            },
            {
                "model": "Llama 3.2 1B Instruct",
                "model_id": "meta.llama3-2-1b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Ultra-lightweight edge deployment, simple text tasks",
                "strengths": "Ultra-compact 1B params, optimized for on-device and edge",
            },
            {
                "model": "Llama 3.1 405B Instruct",
                "model_id": "meta.llama3-1-405b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Tool use, multilingual tasks, complex reasoning, code generation",
                "strengths": "Largest open model (405B params), 128K context, strong across all tasks",
            },
            {
                "model": "Llama 3.1 70B Instruct",
                "model_id": "meta.llama3-1-70b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Code generation, tool use, general reasoning",
                "strengths": "70B params, extended 128K context, supports tool use",
            },
            {
                "model": "Llama 3.1 8B Instruct",
                "model_id": "meta.llama3-1-8b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Edge deployment, fine-tuning, efficient inference",
                "strengths": "Compact 8B params with 128K context, suitable for fine-tuning",
            },
            {
                "model": "Llama 3 70B Instruct",
                "model_id": "meta.llama3-70b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Dialogue, assistant tasks, instruction following",
                "strengths": "70B param instruction-tuned, 8K context, optimized for dialogue",
            },
            {
                "model": "Llama 3 8B Instruct",
                "model_id": "meta.llama3-8b-instruct-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Efficient assistant tasks, smaller infrastructure deployment",
                "strengths": "8B param instruction-tuned, 8K context, efficient deployment",
            },
        ],
    },
    {
        "name": "MiniMax",
        "description": "MiniMax builds large language models with strong multilingual capabilities and competitive reasoning/coding performance.",
        "models": [
            {
                "model": "MiniMax M2.1",
                "model_id": "minimax.minimax-m2.1",
                "input": "Text",
                "output": "Text",
                "use_cases": "General reasoning, coding, instruction following, multilingual tasks",
                "strengths": "Improved reasoning, coding, and instruction following over M2",
            },
            {
                "model": "MiniMax M2",
                "model_id": "minimax.minimax-m2",
                "input": "Text",
                "output": "Text",
                "use_cases": "Multilingual tasks, reasoning, coding",
                "strengths": "Strong multilingual capabilities with solid reasoning and coding benchmarks",
            },
        ],
    },
    {
        "name": "Mistral AI",
        "description": "Mistral AI offers a broad range of models from compact edge-optimized models (3B) to large frontier models (675B), including specialized coding, vision, and speech variants.",
        "models": [
            {
                "model": "Mistral Large 3 (675B)",
                "model_id": "mistral.mistral-large-3-675b-instruct",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Coding, reasoning, multilingual tasks, image understanding",
                "strengths": "675B parameter flagship model with strong coding and reasoning",
            },
            {
                "model": "Devstral 2 123B",
                "model_id": "mistral.devstral-2-123b",
                "input": "Text",
                "output": "Text",
                "use_cases": "Code generation, debugging, refactoring, software engineering",
                "strengths": "123B param model purpose-built for software engineering tasks",
            },
            {
                "model": "Pixtral Large (25.02)",
                "model_id": "mistral.pixtral-large-2502-v1:0",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Visual reasoning, document understanding, image Q&A",
                "strengths": "124B param multimodal model for text and image processing",
            },
            {
                "model": "Magistral Small 2509",
                "model_id": "mistral.magistral-small-2509",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Complex math, coding, logic problems",
                "strengths": "Reasoning model using chain-of-thought for complex problem solving",
            },
            {
                "model": "Voxtral Small 24B",
                "model_id": "mistral.voxtral-small-24b-2507",
                "input": "Speech, Text",
                "output": "Text",
                "use_cases": "High-accuracy transcription, voice understanding",
                "strengths": "24B param speech-to-text model for accurate transcription",
            },
            {
                "model": "Voxtral Mini 3B",
                "model_id": "mistral.voxtral-mini-3b-2507",
                "input": "Speech, Text",
                "output": "Text",
                "use_cases": "Real-time transcription, edge voice understanding",
                "strengths": "Compact 3B speech-to-text model for edge/real-time use",
            },
            {
                "model": "Ministral 14B 3.0",
                "model_id": "mistral.ministral-3-14b-instruct",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "On-device deployment, knowledge and reasoning tasks",
                "strengths": "14B param edge model with strong knowledge/reasoning performance",
            },
            {
                "model": "Ministral 3 8B",
                "model_id": "mistral.ministral-3-8b-instruct",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Edge/mobile deployment, efficient inference",
                "strengths": "8B param compact model for edge and mobile",
            },
            {
                "model": "Ministral 3B",
                "model_id": "mistral.ministral-3-3b-instruct",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "On-device tasks requiring minimal compute",
                "strengths": "Ultra-compact 3B param model for minimal compute environments",
            },
            {
                "model": "Mistral Large (24.02)",
                "model_id": "mistral.mistral-large-2402-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex enterprise tasks, reasoning, multilingual work",
                "strengths": "Strong reasoning, multilingual support, 32K context window",
            },
            {
                "model": "Mistral Large (24.07)",
                "model_id": "mistral.mistral-large-2407-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Enterprise reasoning, coding, multilingual tasks",
                "strengths": "Updated version of Mistral Large with improved capabilities",
            },
            {
                "model": "Mistral Small (24.02)",
                "model_id": "mistral.mistral-small-2402-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Classification, translation, customer support",
                "strengths": "Cost-efficient, optimized for low-latency tasks",
            },
            {
                "model": "Mixtral 8x7B Instruct",
                "model_id": "mistral.mixtral-8x7b-instruct-v0:1",
                "input": "Text",
                "output": "Text",
                "use_cases": "General text tasks, coding, reasoning",
                "strengths": "Sparse MoE (8 experts x 7B), strong performance at fast inference speeds",
            },
            {
                "model": "Mistral 7B Instruct",
                "model_id": "mistral.mistral-7b-instruct-v0:2",
                "input": "Text",
                "output": "Text",
                "use_cases": "Efficient text generation, lightweight deployment",
                "strengths": "7B params with grouped-query and sliding-window attention for efficient long-context inference",
            },
        ],
    },
    {
        "name": "Moonshot AI",
        "description": "Moonshot AI builds frontier reasoning and multimodal models with strong coding and multilingual capabilities.",
        "models": [
            {
                "model": "Kimi K2.5",
                "model_id": "moonshotai.kimi-k2.5",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Reasoning, coding, multilingual tasks, image understanding",
                "strengths": "Multimodal model with improved reasoning, coding, and multilingual capabilities",
            },
            {
                "model": "Kimi K2 Thinking",
                "model_id": "moonshot.kimi-k2-thinking",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex math, coding, logic problems",
                "strengths": "Chain-of-thought reasoning model for complex problem solving",
            },
        ],
    },
    {
        "name": "NVIDIA",
        "description": "NVIDIA's Nemotron Nano family of models are optimized for deployment on NVIDIA GPUs, spanning text-only and vision-language variants.",
        "models": [
            {
                "model": "Nemotron Nano 3 30B",
                "model_id": "nvidia.nemotron-nano-3-30b",
                "input": "Text",
                "output": "Text",
                "use_cases": "Reasoning, coding, general text generation",
                "strengths": "30B params, optimized for NVIDIA GPU deployment, strong reasoning/coding",
            },
            {
                "model": "Nemotron Nano 12B v2 VL",
                "model_id": "nvidia.nemotron-nano-12b-v2",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Image understanding, visual Q&A, multimodal tasks",
                "strengths": "12B param vision-language model for multimodal understanding",
            },
            {
                "model": "Nemotron Nano 9B v2",
                "model_id": "nvidia.nemotron-nano-9b-v2",
                "input": "Text",
                "output": "Text",
                "use_cases": "Text generation, reasoning, coding",
                "strengths": "9B params, efficient inference optimized for NVIDIA hardware",
            },
        ],
    },
    {
        "name": "OpenAI",
        "description": "OpenAI's open-source models on Bedrock include general-purpose text models and specialized safety/guardrail models.",
        "models": [
            {
                "model": "GPT OSS 120B",
                "model_id": "openai.gpt-oss-120b-1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Text generation, coding, reasoning",
                "strengths": "120B param open-source general-purpose model for text generation and coding",
            },
            {
                "model": "GPT OSS 20B",
                "model_id": "openai.gpt-oss-20b-1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Efficient text generation, coding at lower compute cost",
                "strengths": "20B param open-source model balancing performance and efficiency",
            },
            {
                "model": "GPT OSS Safeguard 120B",
                "model_id": "openai.gpt-oss-safeguard-120b",
                "input": "Text",
                "output": "Text",
                "use_cases": "Content moderation, guardrail enforcement in AI pipelines",
                "strengths": "120B param safety model purpose-built for content moderation",
            },
            {
                "model": "GPT OSS Safeguard 20B",
                "model_id": "openai.gpt-oss-safeguard-20b",
                "input": "Text",
                "output": "Text",
                "use_cases": "Lightweight content moderation, guardrail tasks",
                "strengths": "Compact 20B param safety model for lightweight guardrail use",
            },
        ],
    },
    {
        "name": "Qwen",
        "description": "Qwen (Alibaba) models on Bedrock include dense and MoE architectures for general reasoning, coding, and vision-language tasks.",
        "models": [
            {
                "model": "Qwen3 Coder 480B A35B",
                "model_id": "qwen.qwen3-coder-480b-a35b-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Software engineering, code generation, code review",
                "strengths": "Largest coding MoE model (480B total / 35B active) for advanced software engineering",
            },
            {
                "model": "Qwen3 Coder Next",
                "model_id": "qwen.qwen3-coder-next",
                "input": "Text",
                "output": "Text",
                "use_cases": "Code generation, debugging, software engineering",
                "strengths": "Improved code generation, debugging, and SE capabilities",
            },
            {
                "model": "Qwen3 Coder 30B A3B",
                "model_id": "qwen.qwen3-coder-30b-a3b-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Efficient code generation, lightweight coding tasks",
                "strengths": "Compact coding MoE (30B total / 3B active) for efficient code generation",
            },
            {
                "model": "Qwen3 235B A22B",
                "model_id": "qwen.qwen3-235b-a22b-2507-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Text and code generation, general reasoning",
                "strengths": "235B param MoE with 22B active params, 128K context window",
            },
            {
                "model": "Qwen3 VL 235B A22B",
                "model_id": "qwen.qwen3-vl-235b-a22b",
                "input": "Text, Image",
                "output": "Text",
                "use_cases": "Visual reasoning, document understanding, image Q&A",
                "strengths": "Vision-language MoE model for multimodal understanding",
            },
            {
                "model": "Qwen3 32B (dense)",
                "model_id": "qwen.qwen3-32b-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "General reasoning, coding, hybrid thinking (fast + deep)",
                "strengths": "32B dense model with hybrid thinking modes for fast responses or deep reasoning",
            },
            {
                "model": "Qwen3 Next 80B A3B",
                "model_id": "qwen.qwen3-next-80b-a3b",
                "input": "Text",
                "output": "Text",
                "use_cases": "Fast, cost-effective inference for general tasks",
                "strengths": "Efficient MoE with 80B total / 3B active params for fast inference",
            },
        ],
    },
    {
        "name": "Stability AI",
        "description": "Stability AI provides a comprehensive suite of image generation and manipulation models, from text-to-image creation to specialized editing operations.",
        "models": [
            {
                "model": "Stable Diffusion 3.5 Large",
                "model_id": "stability.sd3-5-large-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Text-to-image generation, image-to-image transformation",
                "strengths": "High-quality image generation with latest Stable Diffusion architecture",
            },
            {
                "model": "Stable Image Core 1.0",
                "model_id": "stability.stable-image-core-v1:1",
                "input": "Text",
                "output": "Image",
                "use_cases": "Fast text-to-image generation",
                "strengths": "Core image generation model for quick, quality outputs",
            },
            {
                "model": "Stable Image Ultra 1.0",
                "model_id": "stability.stable-image-ultra-v1:1",
                "input": "Text",
                "output": "Image",
                "use_cases": "Premium text-to-image generation",
                "strengths": "Highest-quality image generation in the Stability AI lineup",
            },
            {
                "model": "Stable Image Inpaint",
                "model_id": "stability.stable-image-inpaint-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Fill masked regions of images with new content",
                "strengths": "Context-aware inpainting guided by text prompts",
            },
            {
                "model": "Stable Image Outpaint",
                "model_id": "stability.stable-outpaint-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Extend images beyond their original boundaries",
                "strengths": "Contextually coherent image extension",
            },
            {
                "model": "Stable Image Erase Object",
                "model_id": "stability.stable-image-erase-object-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Remove unwanted objects from images",
                "strengths": "Object removal with contextually appropriate fill",
            },
            {
                "model": "Stable Image Search & Replace",
                "model_id": "stability.stable-image-search-replace-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Find and replace objects in images",
                "strengths": "Text-guided object replacement in existing images",
            },
            {
                "model": "Stable Image Search & Recolor",
                "model_id": "stability.stable-image-search-recolor-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Change object colors in images",
                "strengths": "Text-guided color change for identified objects",
            },
            {
                "model": "Stable Image Remove Background",
                "model_id": "stability.stable-image-remove-background-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Background removal, foreground isolation",
                "strengths": "Accurate background removal isolating subjects",
            },
            {
                "model": "Stable Image Control Sketch",
                "model_id": "stability.stable-image-control-sketch-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Sketch-guided image generation",
                "strengths": "Generate images guided by sketch inputs for controlled creation",
            },
            {
                "model": "Stable Image Control Structure",
                "model_id": "stability.stable-image-control-structure-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Structure-guided image generation (depth maps, edge detection)",
                "strengths": "Structural input-guided generation for precise control",
            },
            {
                "model": "Stable Image Style Guide",
                "model_id": "stability.stable-image-style-guide-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Generate images matching a reference style",
                "strengths": "Style-consistent generation from reference images and text prompts",
            },
            {
                "model": "Stable Image Style Transfer",
                "model_id": "stability.stable-style-transfer-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Apply artistic style from one image to another",
                "strengths": "Transfer artistic style between images",
            },
            {
                "model": "Stable Image Fast Upscale",
                "model_id": "stability.stable-fast-upscale-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Quick image resolution increase",
                "strengths": "Fast upscaling with minimal processing time",
            },
            {
                "model": "Stable Image Conservative Upscale",
                "model_id": "stability.stable-conservative-upscale-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Detail-preserving image upscaling",
                "strengths": "Resolution increase while preserving original details and style",
            },
            {
                "model": "Stable Image Creative Upscale",
                "model_id": "stability.stable-creative-upscale-v1:0",
                "input": "Text, Image",
                "output": "Image",
                "use_cases": "Upscaling with creative enhancement",
                "strengths": "Upscales while adding creative detail and enhancing visual quality",
            },
        ],
    },
    {
        "name": "TwelveLabs",
        "description": "TwelveLabs specializes in video understanding, providing embedding and generation models for video search, retrieval, and summarization.",
        "models": [
            {
                "model": "Marengo Embed 3.0",
                "model_id": "twelvelabs.marengo-embed-3-0-v1:0",
                "input": "Text, Image, Speech, Video",
                "output": "Embedding",
                "use_cases": "Video search and retrieval, multimodal video understanding",
                "strengths": "Generates vector representations of video content for search/retrieval",
            },
            {
                "model": "Marengo Embed v2.7",
                "model_id": "twelvelabs.marengo-embed-2-7-v1:0",
                "input": "Text, Image, Speech, Video",
                "output": "Embedding",
                "use_cases": "Video search, classification, multimodal video understanding",
                "strengths": "Video embedding model for multimodal understanding and classification",
            },
            {
                "model": "Pegasus v1.2",
                "model_id": "twelvelabs.pegasus-v1-2",
                "input": "Video",
                "output": "Text",
                "use_cases": "Video descriptions, summaries, video Q&A",
                "strengths": "Video-to-text generation for detailed descriptions and summaries",
            },
        ],
    },
    {
        "name": "Writer",
        "description": "Writer builds enterprise-focused LLMs optimized for business writing, content generation, and knowledge work.",
        "models": [
            {
                "model": "Palmyra X5",
                "model_id": "writer.palmyra-x5-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Complex business workflows, agentic tasks, coding",
                "strengths": "Improved reasoning, coding, and agentic capabilities for enterprise",
            },
            {
                "model": "Palmyra X4",
                "model_id": "writer.palmyra-x4-v1:0",
                "input": "Text",
                "output": "Text",
                "use_cases": "Business writing, content generation, knowledge work",
                "strengths": "Optimized for enterprise content generation with strong instruction following",
            },
        ],
    },
    {
        "name": "Z.AI",
        "description": "Z.AI (Zhipu) builds multilingual large language models with competitive reasoning and coding performance.",
        "models": [
            {
                "model": "GLM 4.7",
                "model_id": "zai.glm-4-7",
                "input": "Text",
                "output": "Text",
                "use_cases": "Multilingual tasks, reasoning, coding, knowledge Q&A",
                "strengths": "Strong multilingual capabilities with solid reasoning and coding benchmarks",
            },
            {
                "model": "GLM 4.7 Flash",
                "model_id": "zai.glm-4-7-flash",
                "input": "Text",
                "output": "Text",
                "use_cases": "Low-latency tasks, fast inference, general text generation",
                "strengths": "Lightweight, optimized for fast inference while maintaining strong general capabilities",
            },
        ],
    },
]


HEADER_BG = colors.HexColor("#232F3E")
HEADER_TEXT = colors.white
PROVIDER_BG = colors.HexColor("#FF9900")
PROVIDER_TEXT = colors.white
ROW_ALT_1 = colors.HexColor("#F7F7F7")
ROW_ALT_2 = colors.white
GRID_COLOR = colors.HexColor("#D5D5D5")


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=HEADER_BG,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    )
    provider_title_style = ParagraphStyle(
        "ProviderTitle",
        parent=styles["Heading2"],
        fontSize=14,
        leading=17,
        textColor=HEADER_BG,
        spaceAfter=2,
    )
    provider_desc_style = ParagraphStyle(
        "ProviderDesc",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#111111"),
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=HEADER_TEXT,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    story = []

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Amazon Bedrock Foundation Models", title_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(
        Paragraph(
            "Non-Legacy Models Grouped by Provider -- Use Cases and Strengths",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 0.05 * inch))
    story.append(
        Paragraph(
            f"Source: AWS Documentation (docs.aws.amazon.com/bedrock) | Generated {datetime.now().strftime('%B %d, %Y')}",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    col_widths = [
        1.35 * inch,
        1.7 * inch,
        0.65 * inch,
        0.65 * inch,
        2.2 * inch,
        2.85 * inch,
    ]

    headers = ["Model", "Model ID", "Input", "Output", "Use Cases", "Strengths"]
    header_row = [Paragraph(h, header_cell_style) for h in headers]

    for provider in PROVIDERS:
        story.append(Paragraph(provider["name"], provider_title_style))
        story.append(Paragraph(provider["description"], provider_desc_style))

        table_data = [header_row]

        for model in provider["models"]:
            row = [
                Paragraph(model["model"], cell_bold_style),
                Paragraph(model["model_id"], cell_style),
                Paragraph(model["input"], cell_style),
                Paragraph(model["output"], cell_style),
                Paragraph(model["use_cases"], cell_style),
                Paragraph(model["strengths"], cell_style),
            ]
            table_data.append(row)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
            ("LINEBELOW", (0, 0), (-1, 0), 1, HEADER_BG),
        ]

        for i in range(1, len(table_data)):
            bg = ROW_ALT_1 if i % 2 == 0 else ROW_ALT_2
            style_commands.append(("BACKGROUND", (0, i), (-1, i), bg))

        table.setStyle(TableStyle(style_commands))

        story.append(table)
        story.append(Spacer(1, 0.25 * inch))

    story.append(Spacer(1, 0.2 * inch))

    footnote_style = ParagraphStyle(
        "Footnote",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#666666"),
    )
    story.append(
        Paragraph(
            "Notes: This document lists only non-legacy (Active) foundation models available on Amazon Bedrock. "
            "Legacy and End-of-Life models are excluded. Model availability varies by AWS Region. "
            "For the latest information, refer to the official AWS documentation at "
            "docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html",
            footnote_style,
        )
    )

    doc.build(story)
    return output_path


if __name__ == "__main__":
    output = build_pdf("bedrock_foundation_models.pdf")
    print(f"PDF generated: {output}")
