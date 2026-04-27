import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';
import '../models/scan_result.dart';
import '../models/user.dart';
import '../models/app_notification.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;

  // ==================== TOKEN MANAGEMENT ====================

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(Constants.tokenKey);
  }

  Future<void> saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(Constants.tokenKey, token);
  }

  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(Constants.tokenKey);
  }

  bool get isLoggedIn => _token != null;

  Map<String, String> get _headers {
    return {
      'Content-Type': 'application/json',
      if (_token != null) 'Authorization': 'Bearer $_token',
    };
  }

  // Ensure token is loaded before making authenticated requests
  Future<void> _ensureToken() async {
    if (_token == null) {
      await loadToken();
    }
  }

  // ==================== AUTH ====================

  Future<User> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.loginEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': email,
          'password': password,
        }),
      ).timeout(const Duration(seconds: 10));

      final data = json.decode(response.body);

      if (response.statusCode == 200) {
        final token = data['access_token'];
        await saveToken(token);
        return User.fromJson(data['user'], token: token);
      } else {
        throw Exception(data['error'] ?? 'Login failed');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Connection error: $e');
    }
  }

  Future<User> register(String name, String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.registerEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'name': name,
          'email': email,
          'password': password,
        }),
      ).timeout(const Duration(seconds: 10));

      final data = json.decode(response.body);

      if (response.statusCode == 201) {
        final token = data['access_token'];
        await saveToken(token);
        return User.fromJson(data['user'], token: token);
      } else {
        throw Exception(data['error'] ?? 'Registration failed');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Connection error: $e');
    }
  }

  Future<User> loginWithGoogle(String idToken) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.googleEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'idToken': idToken,
        }),
      ).timeout(const Duration(seconds: 10));

      final data = json.decode(response.body);

      if (response.statusCode == 200) {
        final token = data['access_token'];
        await saveToken(token);
        return User.fromJson(data['user'], token: token);
      } else {
        throw Exception(data['error'] ?? 'Google login failed');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Connection error: $e');
    }
  }

  Future<User?> getCurrentUser() async {
    try {
      await loadToken();
      if (_token == null) return null;

      final response = await http.get(
        Uri.parse('${Constants.baseUrl}${Constants.meEndpoint}'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return User.fromJson(data['user'], token: _token);
      } else {
        await clearToken();
        return null;
      }
    } catch (e) {
      return null;
    }
  }

  Future<void> logout() async {
    await clearToken();
  }

  Future<void> updateSettings({
    String? fcmToken,
    bool? pushEnabled,
    bool? emailEnabled,
  }) async {
    try {
      await _ensureToken();
      if (_token == null) return;

      final body = {};
      if (fcmToken != null) body['fcm_token'] = fcmToken;
      if (pushEnabled != null) body['push_enabled'] = pushEnabled;
      if (emailEnabled != null) body['email_enabled'] = emailEnabled;

      if (body.isEmpty) return;

      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/api/auth/settings'),
        headers: _headers,
        body: json.encode(body),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        print('Failed to update settings: ${response.body}');
      }
    } catch (e) {
      print('Error updating settings: $e');
    }
  }

  // ==================== SCAN ====================

  Future<ScanResult> analyzePose(List<List<List<double>>> frames) async {
    try {
      await loadToken(); // Always reload from storage to ensure token is fresh
      
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.predictEndpoint}'),
        headers: _headers,
        body: json.encode({'frames': frames}),
      ).timeout(const Duration(seconds: 10));

      print('API Response Status: ${response.statusCode}');
      print('API Response Body: ${response.body}');

      if (response.statusCode == 200) {
        return ScanResult.fromJson(json.decode(response.body));
      } else {
        throw Exception('Analysis failed: ${json.decode(response.body)['error']}');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Connection error: $e');
    }
  }

  Future<ScanResult> uploadVideoForAnalysis(String videoPath) async {
    try {
      await loadToken();
      
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${Constants.baseUrl}${Constants.analyzeVideoEndpoint}'),
      );
      
      if (_token != null) {
        request.headers['Authorization'] = 'Bearer $_token';
      }
      
      if (kIsWeb) {
        // On Web, we must fetch the bytes from the blob URL first
        final response = await http.get(Uri.parse(videoPath));
        final bytes = response.bodyBytes;
        request.files.add(
          http.MultipartFile.fromBytes(
            'video',
            bytes,
            filename: 'recording.mp4',
          ),
        );
      } else {
        request.files.add(
          await http.MultipartFile.fromPath('video', videoPath),
        );
      }
      
      final streamedResponse = await request.send().timeout(const Duration(seconds: 60));
      final response = await http.Response.fromStream(streamedResponse);
      
      print('API Response Status: ${response.statusCode}');
      print('API Response Body: ${response.body}');

      if (response.statusCode == 200) {
        return ScanResult.fromJson(json.decode(response.body));
      } else {
        final errorMsg = json.decode(response.body)['error'] ?? 'Unknown server error';
        throw Exception('Video analysis failed: $errorMsg');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Upload error: $e');
    }
  }

  Future<List<ScanResult>> getHistory({int page = 1, int perPage = 20}) async {
    try {
      await loadToken(); // Always reload from storage to ensure token is fresh
      
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}${Constants.scansEndpoint}?page=$page&per_page=$perPage'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final scans = data['scans'] as List;
        return scans.map((s) => ScanResult.fromJson(Map<String, dynamic>.from(s as Map))).toList();
      } else {
        // Return empty list instead of throwing for 422 or other errors
        return [];
      }
    } catch (e) {
      // Return empty list on error
      return [];
    }
  }

  Future<void> deleteScan(String scanId) async {
    try {
      await _ensureToken();
      
      final response = await http.delete(
        Uri.parse('${Constants.baseUrl}${Constants.scansEndpoint}/$scanId'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        throw Exception('Failed to delete scan');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Connection error: $e');
    }
  }

  Future<Map<String, dynamic>> getStats() async {
    try {
      await loadToken(); // Always reload from storage to ensure token is fresh
      
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}${Constants.statsEndpoint}'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final stats = data['stats'];
        // Cast LinkedMap<dynamic,dynamic> -> Map<String,dynamic>
        return Map<String, dynamic>.from(stats as Map);
      } else {
        // Return empty stats instead of throwing for 422 or other errors
        return {'total_scans': 0, 'by_prediction': {}};
      }
    } catch (e) {
      // Return empty stats on error
      return {'total_scans': 0, 'by_prediction': {}};
    }
  }

  // ==================== HISTORY WIPING ====================

  Future<void> clearHistory() async {
    try {
      await loadToken();
      final response = await http.delete(
        Uri.parse('${Constants.baseUrl}/api/scans/all'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        throw Exception('Failed to clear history: ${response.body}');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }

  // ==================== HEALTH CHECK ====================

  Future<bool> checkConnection() async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}${Constants.healthEndpoint}'),
      ).timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // ==================== NOTIFICATIONS ====================

  Future<Map<String, dynamic>> getNotifications() async {
    try {
      await loadToken();
      
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/api/notifications'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final unreadCount = data['unread_count'] as int;
        final notifsList = data['notifications'] as List;
        
        return {
          'unread_count': unreadCount,
          'notifications': notifsList.map((n) => AppNotification.fromJson(Map<String, dynamic>.from(n as Map))).toList(),
        };
      } else {
        return {'unread_count': 0, 'notifications': <AppNotification>[]};
      }
    } catch (e) {
      return {'unread_count': 0, 'notifications': <AppNotification>[]};
    }
  }

  Future<void> markNotificationsRead(List<int> ids) async {
    try {
      await _ensureToken();
      await http.post(
        Uri.parse('${Constants.baseUrl}/api/notifications/read'),
        headers: _headers,
        body: json.encode({'notification_ids': ids}),
      ).timeout(const Duration(seconds: 10));
    } catch (e) {
      print('Failed to mark read: $e');
    }
  }
  
  Future<void> logExport(String exportType) async {
    try {
      await _ensureToken();
      await http.post(
        Uri.parse('${Constants.baseUrl}/api/log_export'),
        headers: _headers,
        body: json.encode({'export_type': exportType}),
      );
    } catch (e) {
      print('Failed to log export: $e');
    }
  }
}
