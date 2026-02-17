import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/user.dart';
import '../widgets/custom_button.dart';
import 'welcome_screen.dart';

class ProfileScreen extends StatelessWidget {
  final User user;

  const ProfileScreen({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            // Profile Header
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.person,
                size: 50,
                color: AppTheme.primaryColor,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              user.name,
              style: Theme.of(context).textTheme.displaySmall,
            ),
            const SizedBox(height: 4),
            Text(
              user.email,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
            ),
            const SizedBox(height: 32),
            
            // Statistics
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppTheme.cardColor,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '📊 Statistics',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 16),
                  _buildStatRow(context, 'Total Scans', '12'),
                  _buildStatRow(context, 'Normal Results', '11'),
                  _buildStatRow(context, 'Flagged Results', '1'),
                  _buildStatRow(context, 'Avg Detection', '97.8%'),
                  _buildStatRow(context, 'Member Since', 'Jan 2024'),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Settings Menu
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppTheme.cardColor,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  _buildMenuItem(
                    context,
                    Icons.person_outline,
                    'Edit Profile',
                    () {},
                  ),
                  _buildDivider(),
                  _buildMenuItem(
                    context,
                    Icons.notifications_outlined,
                    'Notifications',
                    () {},
                  ),
                  _buildDivider(),
                  _buildMenuItem(
                    context,
                    Icons.lock_outline,
                    'Privacy Settings',
                    () {},
                  ),
                  _buildDivider(),
                  _buildMenuItem(
                    context,
                    Icons.help_outline,
                    'Help & Support',
                    () {},
                  ),
                  _buildDivider(),
                  _buildMenuItem(
                    context,
                    Icons.description_outlined,
                    'Terms & Privacy',
                    () {},
                  ),
                  _buildDivider(),
                  _buildMenuItem(
                    context,
                    Icons.info_outline,
                    'About SafePose',
                    () {},
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            
            // Logout Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (_) => const WelcomeScreen()),
                    (route) => false,
                  );
                },
                icon: const Icon(Icons.logout, color: AppTheme.errorColor),
                label: const Text(
                  'Log Out',
                  style: TextStyle(color: AppTheme.errorColor),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppTheme.errorColor),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(
    BuildContext context,
    IconData icon,
    String title,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.textSecondary),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                title,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: AppTheme.textSecondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(
      height: 1,
      indent: 56,
      color: AppTheme.surfaceColor,
    );
  }
}
