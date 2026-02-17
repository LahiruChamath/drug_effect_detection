class Constants {
  // API Configuration
  // Change this to your MacBook's IP when testing
  static const String baseUrl = "http://192.168.1.100:8000";
  
  // For localhost testing on iOS simulator
  // static const String baseUrl = "http://localhost:8000";
  
  // API Endpoints
  static const String loginEndpoint = "/api/auth/login";
  static const String registerEndpoint = "/api/auth/register";
  static const String analyzeEndpoint = "/api/scan/analyze";
  static const String historyEndpoint = "/api/scan/history";
  
  // App Configuration
  static const int recordingDuration = 10; // seconds
  static const double minDetectionRate = 0.7; // 70%
  
  // Storage Keys
  static const String tokenKey = "auth_token";
  static const String userKey = "user_data";
}
