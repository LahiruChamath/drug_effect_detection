class Constants {
  // API Configuration
  // Use 127.0.0.1 for Chrome, use your IP for real device
  static const String baseUrl = "http://127.0.0.1:5001";
  
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
