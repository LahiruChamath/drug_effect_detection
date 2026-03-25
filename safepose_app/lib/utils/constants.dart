import 'package:flutter/foundation.dart' show kIsWeb;

class Constants {
  // API Configuration
  // Automatically uses localhost for web (Chrome) and Mac's IP for physical devices
  static const String _webUrl = "http://127.0.0.1:5001";
  static const String _deviceUrl = "http://192.168.1.93:5001";
  static String get baseUrl => kIsWeb ? _webUrl : _deviceUrl;
  
  // API Endpoints
  static const String loginEndpoint = "/api/auth/login";
  static const String registerEndpoint = "/api/auth/register";
  static const String meEndpoint = "/api/auth/me";
  static const String predictEndpoint = "/api/predict";
  static const String scansEndpoint = "/api/scans";
  static const String statsEndpoint = "/api/stats";
  static const String healthEndpoint = "/api/health";
  
  // App Configuration
  static const int recordingDuration = 10; // seconds
  static const int targetFrames = 150; // 5 seconds at 30fps
  static const double minDetectionRate = 0.7; // 70%
  
  // Storage Keys
  static const String tokenKey = "auth_token";
  static const String userKey = "user_data";
}
