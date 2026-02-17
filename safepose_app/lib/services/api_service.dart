import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import '../models/scan_result.dart';
import '../models/user.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;

  void setToken(String token) {
    _token = token;
  }

  Map<String, String> get _headers {
    return {
      'Content-Type': 'application/json',
      if (_token != null) 'Authorization': 'Bearer $_token',
    };
  }

  // ==================== AUTH ====================

  Future<User> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.loginEndpoint}'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'email': email,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _token = data['token'];
        return User.fromJson(data['user']);
      } else {
        throw Exception('Login failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }

  Future<bool> register(String name, String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}${Constants.registerEndpoint}'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'name': name,
          'email': email,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        return true;
      } else {
        throw Exception('Registration failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }

  // ==================== SCAN ====================

  Future<ScanResult> analyzeVideo(File videoFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${Constants.baseUrl}${Constants.analyzeEndpoint}'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('video', videoFile.path),
      );

      if (_token != null) {
        request.headers['Authorization'] = 'Bearer $_token';
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return ScanResult.fromJson(data);
      } else {
        throw Exception('Analysis failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }

  Future<List<ScanResult>> getHistory() async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}${Constants.historyEndpoint}'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final scans = data['scans'] as List;
        return scans.map((s) => ScanResult.fromJson(s)).toList();
      } else {
        throw Exception('Failed to load history');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }

  // ==================== HEALTH CHECK ====================

  Future<bool> checkConnection() async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/api/health'),
      ).timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
