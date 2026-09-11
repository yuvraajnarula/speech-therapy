# Speech Therapy

A full-stack application for speech therapy assistance, combining a Python backend with a React TypeScript frontend.

## Project Structure

```
speech-therapy/
├── backend/
│   ├── services/
│   │   ├── agent_orchestrator.py      # Orchestrates therapy agents
│   │   ├── mcp_server.py              # MCP (Model Context Protocol) server
│   │   ├── recover_audio.py           # Audio recovery utilities
│   │   └── repoint_jsonl.py           # JSONL data management
│   ├── deprecated_app_v1.py           # Legacy application (deprecated)
│   ├── sarvam_train.jsonl             # Training data for Sarvam
│   ├── whisper_train.jsonl            # Training data for Whisper
│   ├── whisper_train_clean.jsonl      # Cleaned Whisper training data
│   └── whisper_train_fixed.jsonl      # Fixed Whisper training data
│
├── frontend/
│   ├── src/                           # React/TypeScript source code
│   ├── public/                        # Static assets
│   ├── package.json                   # Frontend dependencies and scripts
│   ├── vite.config.ts                 # Vite build configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   └── README.md                      # Frontend-specific documentation
│
└── .vscode/                           # VS Code settings
```

## Technology Stack

### Backend
- **Language**: Python
- **Key Components**:
  - `agent_orchestrator.py` - Agent coordination and orchestration
  - `mcp_server.py` - Model Context Protocol server implementation
  - `recover_audio.py` - Audio processing and recovery
  - `repoint_jsonl.py` - Data pipeline management

### Frontend
- **Framework**: React 19.2.6
- **Language**: TypeScript (~6.0.2)
- **Build Tool**: Vite 8.0.12
- **Development Tools**: ESLint, TypeScript ESLint

## Language Composition

- **Python**: 61.6%
- **TypeScript**: 22.4%
- **CSS**: 13.4%
- **JavaScript**: 1.6%
- **HTML**: 1.0%

## Getting Started

### Frontend Setup

```bash
cd frontend
npm install
```

#### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

### Backend Setup

The backend includes:
- Model training data in JSONL format for both Sarvam and Whisper models
- An MCP server for protocol-based communication
- Agent orchestration for therapy workflow coordination
- Audio processing utilities

## Features

- **Agent Orchestration**: Coordinate multiple therapy agents
- **Audio Processing**: Recover and process audio data
- **Model Training**: Support for Sarvam and Whisper model fine-tuning
- **MCP Server**: Protocol-based communication interface
- **React Frontend**: Modern, responsive UI for therapy sessions

## Development

This is a full-stack application with clear separation between frontend and backend services. The backend provides APIs and services that the frontend consumes through the MCP server interface.

## License

Not specified

## Contributing

Contributions are welcome! Please ensure code follows the project's ESLint configuration.

---

For frontend-specific details, see [frontend/README.md](./frontend/README.md)
