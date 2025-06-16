# Life OS Flutter - Your AI Life Assistant

A cross-platform AI assistant that replaces Siri and Google Assistant, helping you capture, organize, and reason across all your life data.

## 🚀 Features

### Core Capabilities
- **🎙️ Voice Assistant**: Background voice recognition with "Hey Life OS" wake word
- **🧠 AI-Powered**: Gemini 2.0 Flash for multimodal processing
- **📱 Cross-Platform**: Native iOS and Android with platform-specific optimizations
- **🔍 Semantic Search**: Vector database for intelligent memory retrieval
- **🔗 Knowledge Graph**: Automatic relationship mapping between memories
- **🔒 Privacy-First**: Local storage with optional cloud sync

### Platform Integration

#### iOS
- **Siri Shortcuts**: Deep integration with iOS Shortcuts app
- **App Intents**: System-level integration (iOS 16+)
- **Live Activities**: Real-time status on Dynamic Island
- **Focus Filters**: Context-aware capture modes

#### Android
- **Assistant Replacement**: Can replace Google Assistant as default
- **Accessibility Service**: System-wide content capture
- **Direct Share**: Quick capture from any app
- **Floating Bubble**: Always-accessible capture interface

## 📋 Prerequisites

- Flutter SDK 3.16 or higher
- Dart SDK 3.0 or higher
- For iOS: Xcode 15+ and iOS 14+
- For Android: Android Studio and Android SDK 21+
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/life-os-flutter.git
   cd life-os-flutter
   ```

2. **Install Flutter dependencies**
   ```bash
   flutter pub get
   ```

3. **Set up API keys**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Platform-specific setup**

   **iOS:**
   ```bash
   cd ios
   pod install
   ```

   **Android:**
   - Open `android/local.properties`
   - Add: `gemini.api.key=your_gemini_api_key_here`

## 🏃‍♂️ Running the App

### Development
```bash
# Run on iOS simulator
flutter run -d ios

# Run on Android emulator
flutter run -d android

# Run on physical device
flutter run
```

### Building for Release

**iOS:**
```bash
flutter build ios --release
# Then archive and upload via Xcode
```

**Android:**
```bash
flutter build apk --release
# or for App Bundle
flutter build appbundle --release
```

## 🎯 Usage

### Voice Commands
- **"Hey Life OS"** - Activate the assistant
- **"Capture [your thought]"** - Save a memory
- **"Search for [query]"** - Search your memories
- **"What did I do today?"** - Get daily summary
- **"Add task [description]"** - Create a task

### Quick Actions
- **Long press home button** (Android) - Activate Life OS
- **"Hey Siri, capture thought with Life OS"** (iOS) - Quick capture via Siri

## 🏗️ Architecture

```
lib/
├── core/               # Core business logic
│   ├── constants/      # App constants
│   ├── errors/         # Error handling
│   └── utils/          # Utilities
├── features/           # Feature modules
│   ├── assistant/      # Voice assistant
│   ├── capture/        # Memory capture
│   ├── search/         # Search functionality
│   └── settings/       # App settings
├── shared/             # Shared components
│   ├── services/       # Services (AI, DB, etc.)
│   ├── theme/          # App theming
│   └── widgets/        # Reusable widgets
└── main.dart          # App entry point
```

## 🔧 Configuration

### Permissions Required

**iOS (Info.plist):**
- `NSMicrophoneUsageDescription`
- `NSSpeechRecognitionUsageDescription`
- `NSCameraUsageDescription`
- `NSPhotoLibraryUsageDescription`

**Android (AndroidManifest.xml):**
- `android.permission.RECORD_AUDIO`
- `android.permission.INTERNET`
- `android.permission.CAMERA`
- `android.permission.SYSTEM_ALERT_WINDOW`

### Background Service Setup

The app uses `flutter_background_service` for continuous voice recognition. Configure wake lock and battery optimization exemptions for best performance.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Generative AI team for Gemini API
- Flutter team for the amazing framework
- [flutter_background_service](https://pub.dev/packages/flutter_background_service) for background processing
- [speech_to_text](https://pub.dev/packages/speech_to_text) for voice recognition

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/life-os-flutter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/life-os-flutter/discussions)
- **Email**: support@lifeos.app

---

Built with ❤️ using Flutter 