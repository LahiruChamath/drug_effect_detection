import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/custom_button.dart';
import 'login_screen.dart';
import 'signup_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            children: [
              const Spacer(flex: 2),
              
              // Logo
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: Image.asset(
                    'assets/images/app_icon.png',
                    fit: BoxFit.contain,
                  ),
                ),
              ),
              const SizedBox(height: 32),
              
              // Title
              Text(
                'Welcome to SafePose',
                style: Theme.of(context).textTheme.displaySmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              
              Text(
                'Analyze movement patterns with complete privacy protection',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              
              // Features
              _buildFeatureRow(
                context,
                Icons.videocam_rounded,
                'Capture',
                'Record 10s video',
              ),
              const SizedBox(height: 16),
              _buildFeatureRow(
                context,
                Icons.psychology_rounded,
                'Analyze',
                'AI-powered detection',
              ),
              const SizedBox(height: 16),
              _buildFeatureRow(
                context,
                Icons.lock_rounded,
                'Private',
                'Only skeleton data stored',
              ),
              
              const Spacer(flex: 2),
              
              // Buttons
              CustomButton(
                text: 'Get Started',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const SignupScreen()),
                  );
                },
              ),
              const SizedBox(height: 12),
              CustomButton(
                text: 'I already have an account',
                isOutlined: true,
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                  );
                },
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureRow(
    BuildContext context,
    IconData icon,
    String title,
    String subtitle,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.primaryLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: AppTheme.primaryColor,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.labelLarge,
              ),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
