import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/api_service.dart';
import '../../models/user.dart';
import 'package:shared_preferences/shared_preferences.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _pushEnabled = true;
  bool _emailEnabled = false;
  bool _isLoading = true;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);
    try {
      final user = await _apiService.getCurrentUser();
      if (user != null) {
        setState(() {
          _pushEnabled = user.pushEnabled;
          _emailEnabled = user.emailEnabled;
        });
      } else {
        // Fallback to local if offline or not logged in
        final prefs = await SharedPreferences.getInstance();
        setState(() {
          _pushEnabled = prefs.getBool('notifications_push') ?? true;
          _emailEnabled = prefs.getBool('notifications_email') ?? false;
        });
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _updateSettings({bool? push, bool? email}) async {
    // 1. Update UI and Local Storage immediately for responsiveness
    final prefs = await SharedPreferences.getInstance();
    if (push != null) {
      setState(() => _pushEnabled = push);
      await prefs.setBool('notifications_push', push);
    }
    if (email != null) {
      setState(() => _emailEnabled = email);
      await prefs.setBool('notifications_email', email);
    }

    // 2. Sync with Backend
    await _apiService.updateSettings(
      pushEnabled: push,
      emailEnabled: email,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Notifications', style: TextStyle(color: AppTheme.textPrimary)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppTheme.textPrimary),
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryColor))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Manage how SafePose alerts you about your daily scans, analytical models, and account activity.',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
                ),
                const SizedBox(height: 24),
                _buildSwitch(
                  'Allow Push Notifications', 
                  'Get instant alerts on your device', 
                  _pushEnabled, 
                  (val) => _updateSettings(push: val)
                ),
                const Divider(),
                _buildSwitch(
                  'Email Notifications', 
                  'Receive results and summaries via email', 
                  _emailEnabled, 
                  (val) => _updateSettings(email: val)
                ),
              ],
            ),
    );
  }

  Widget _buildSwitch(String title, String subtitle, bool value, ValueChanged<bool> onChanged) {
    return SwitchListTile(
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 13)),
      value: value,
      activeColor: AppTheme.primaryColor,
      onChanged: onChanged,
    );
  }
}
