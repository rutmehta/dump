# Life OS Android

Life OS is a revolutionary Android productivity application that acts as your personal AI secretary. It captures and organizes all forms of data (text, audio, video, images, documents) using advanced AI to boost your productivity 100x.

## 🌟 Features

- **Multimodal Capture**: Capture text, audio, images, videos, and documents seamlessly
- **AI-Powered Processing**: Uses Google's Gemini 2.5 Pro for intelligent data processing
- **Smart Search**: Hybrid search combining semantic understanding and keyword matching
- **Automatic Organization**: AI automatically categorizes and tags your memories
- **System Integration**: Deep Android integration with share menu, quick tiles, and assistant
- **Privacy First**: Optional on-device processing with Gemini Nano

## 🚀 Getting Started

### Prerequisites

- Android Studio Hedgehog (2023.1.1) or newer
- Android SDK 34 or higher
- JDK 17 or higher
- A Google AI API key (get one at https://makersuite.google.com/app/apikey)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd life-os-android
   ```

2. **Configure API Keys**
   ```bash
   cp local.properties.template local.properties
   ```
   Edit `local.properties` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Build and Run**
   - Open the project in Android Studio
   - Sync project with Gradle files
   - Run the app on an emulator or physical device (API 26+)

## 🏗️ Architecture

The app follows Clean Architecture principles with MVVM pattern:

```
app/
├── data/           # Data layer (Repository, Local/Remote data sources)
│   ├── local/      # Room database, DAOs, entities
│   └── repository/ # Repository implementations
├── domain/         # Business logic layer
│   ├── models/     # Domain models
│   └── usecases/   # Business use cases
├── ui/             # Presentation layer
│   ├── screens/    # Compose screens and ViewModels
│   └── theme/      # Material You theme
├── services/       # Android services (AI, notifications, etc.)
└── di/             # Dependency injection modules
```

### Tech Stack

- **UI**: Jetpack Compose with Material You
- **Architecture**: MVVM + Clean Architecture
- **DI**: Hilt
- **Database**: Room
- **AI**: Google AI SDK (Gemini)
- **Async**: Kotlin Coroutines + Flow
- **Navigation**: Navigation Compose

## 📱 Core Screens

### 1. Capture Screen
- Quick capture interface for all data types
- Voice recording with transcription
- Camera integration for photos/videos
- Document scanning

### 2. Search Screen
- Semantic search using AI embeddings
- Keyword search with filters
- Hybrid search combining both approaches
- Timeline view of memories

### 3. Insights Screen (Coming Soon)
- AI-generated insights from your data
- Pattern recognition
- Productivity analytics
- Suggested actions

### 4. Settings Screen (Coming Soon)
- Privacy controls
- AI processing preferences
- Data export/import
- Account management

## 🔧 Development

### Building Debug APK
```bash
./gradlew assembleDebug
```

### Running Tests
```bash
./gradlew test
./gradlew connectedAndroidTest
```

### Code Style
The project uses Kotlin coding conventions. Run ktlint before committing:
```bash
./gradlew ktlintCheck
./gradlew ktlintFormat
```

## 🔐 Security & Privacy

- All data is encrypted using AES-256
- Biometric authentication support
- Optional on-device processing
- No data leaves device without explicit permission
- Full GDPR compliance

## 🚦 Roadmap

### Phase 1: Foundation ✅
- Basic capture functionality
- Local storage with Room
- Simple search

### Phase 2: AI Integration (In Progress)
- Gemini 2.5 Pro integration
- Smart categorization
- Entity extraction

### Phase 3: Memory System
- Vector database for semantic search
- Knowledge graph
- Context building

### Phase 4: System Integration
- Android Assistant replacement
- Quick Settings tile
- Widget support

### Phase 5: Advanced Features
- MCP (Model Context Protocol) support
- Cross-device sync
- Automation workflows

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines (coming soon).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google AI team for Gemini API
- Android Jetpack team for amazing tools
- The open-source community