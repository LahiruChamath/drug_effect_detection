import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import 'welcome_screen.dart';

class ProfileScreen extends StatefulWidget {
  final User user;

  const ProfileScreen({super.key, required this.user});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _stats;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final stats = await ApiService().getStats();
      if (mounted) {
        setState(() {
          _stats = stats;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Log Out'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.errorColor),
            child: const Text('Log Out', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await ApiService().logout();
      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const WelcomeScreen()),
          (route) => false,
        );
      }
    }
  }

  Future<void> _showCameraPreferencesDialog() async {
    final prefs = await SharedPreferences.getInstance();
    String currentPreference = prefs.getString('camera_preference') ?? 'back';

    if (!mounted) return;

    await showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: const Text('Camera Default', style: TextStyle(fontWeight: FontWeight.bold)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  RadioListTile<String>(
                    title: const Text('Back Camera (Main)'),
                    value: 'back',
                    groupValue: currentPreference,
                    activeColor: AppTheme.primaryColor,
                    onChanged: (value) async {
                      setDialogState(() => currentPreference = value!);
                      await prefs.setString('camera_preference', value!);
                      if (context.mounted) Navigator.pop(context);
                    },
                  ),
                  RadioListTile<String>(
                    title: const Text('Front Camera (Selfie)'),
                    value: 'front',
                    groupValue: currentPreference,
                    activeColor: AppTheme.primaryColor,
                    onChanged: (value) async {
                      setDialogState(() => currentPreference = value!);
                      await prefs.setString('camera_preference', value!);
                      if (context.mounted) Navigator.pop(context);
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  int get _totalScans => _stats?['total_scans'] ?? 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadStats,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                const SizedBox(height: 12),

                // ==========================================
                // PROFILE HEADER
                // ==========================================
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: AppTheme.cardShadow,
                  ),
                  child: Column(
                    children: [
                      // Avatar
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              AppTheme.primaryColor,
                              AppTheme.primaryDark,
                            ],
                          ),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            widget.user.name.isNotEmpty
                                ? widget.user.name[0].toUpperCase()
                                : '?',
                            style: const TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        widget.user.name,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        widget.user.email,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppTheme.textSecondary,
                            ),
                      ),
                      const SizedBox(height: 16),
                      // Quick stats: scan count + streak
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildProfileStat(
                            '$_totalScans',
                            'Scans',
                            Icons.analytics_outlined,
                          ),
                          const SizedBox(width: 32),
                          _buildProfileStat(
                            _getStreak(),
                            'Streak',
                            Icons.local_fire_department,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // ==========================================
                // SETTINGS
                // ==========================================
                _buildSection(
                  title: 'Settings',
                  children: [
                    _buildMenuItem(
                      Icons.notifications_outlined,
                      'Notifications',
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Notifications'),
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.camera_alt_outlined,
                      'Camera Preferences',
                      trailing: _buildChevron(),
                      onTap: _showCameraPreferencesDialog,
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.lock_outline,
                      'Privacy Settings',
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Privacy Settings'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // ==========================================
                // DATA
                // ==========================================
                _buildSection(
                  title: 'Data',
                  children: [
                    _buildMenuItem(
                      Icons.picture_as_pdf_outlined,
                      'Export as PDF',
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Export as PDF'),
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.table_chart_outlined,
                      'Export as CSV',
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Export as CSV'),
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.delete_outline,
                      'Clear History',
                      textColor: AppTheme.errorColor,
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Clear History'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // ==========================================
                // ABOUT
                // ==========================================
                _buildSection(
                  title: 'About',
                  children: [
                    _buildMenuItem(
                      Icons.help_outline,
                      'Help & Support',
                      trailing: _buildChevron(),
                      onTap: _showHelpDialog,
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.info_outline,
                      'About SafePose',
                      trailing: _buildChevron(),
                      onTap: _showAboutDialog,
                    ),
                    _buildDivider(),
                    _buildMenuItem(
                      Icons.star_outline,
                      'Rate the App',
                      trailing: _buildChevron(),
                      onTap: () => _showComingSoon('Rate the App'),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // ==========================================
                // LOGOUT
                // ==========================================
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _logout,
                    icon: const Icon(Icons.logout, color: AppTheme.errorColor, size: 20),
                    label: const Text(
                      'Log Out',
                      style: TextStyle(color: AppTheme.errorColor, fontWeight: FontWeight.w600),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppTheme.errorColor),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'SafePose v1.0.0',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textTertiary,
                      ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ==========================================
  // HELPERS
  // ==========================================
  Widget _buildProfileStat(String value, String label, IconData icon) {
    return Column(
      children: [
        Row(
          children: [
            Icon(icon, size: 16, color: AppTheme.primaryColor),
            const SizedBox(width: 4),
            Text(
              value,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppTheme.primaryColor,
              ),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: AppTheme.textTertiary),
        ),
      ],
    );
  }

  String _getStreak() {
    // Simple streak: show total scans as a basic metric
    // A real streak counter would need date tracking
    return '$_totalScans';
  }

  Widget _buildSection({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          child: Text(
            title.toUpperCase(),
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.textTertiary,
              letterSpacing: 1.2,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: AppTheme.cardShadow,
          ),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildMenuItem(
    IconData icon,
    String title, {
    Widget? trailing,
    Color? textColor,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: (textColor ?? AppTheme.primaryColor).withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                icon,
                color: textColor ?? AppTheme.textSecondary,
                size: 20,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                title,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: textColor ?? AppTheme.textPrimary,
                ),
              ),
            ),
            if (trailing != null) trailing,
          ],
        ),
      ),
    );
  }

  Widget _buildChevron() {
    return const Icon(Icons.chevron_right, color: AppTheme.textTertiary, size: 20);
  }

  Widget _buildDivider() {
    return Divider(
      height: 1,
      indent: 66,
      color: AppTheme.dividerColor,
    );
  }

  void _showComingSoon(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature — Coming soon!'),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Help & Support'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Need help? Contact us:'),
            SizedBox(height: 16),
            Text('📧 support@safepose.app'),
            SizedBox(height: 8),
            Text('📱 1-800-SAFEPOSE'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('About SafePose'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'SafePose uses advanced AI to analyze body movement patterns for safety screening.',
            ),
            SizedBox(height: 16),
            Text('Version: 1.0.0'),
            Text('Model: XGBoost (85% accuracy)'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
