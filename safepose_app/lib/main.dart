import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'theme/app_theme.dart';
import 'screens/splash_screen.dart';
import 'screens/welcome_screen.dart';
import 'screens/login_screen.dart';
import 'screens/signup_screen.dart';
import 'screens/home_screen.dart';
import 'screens/scan_instructions_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/analyzing_screen.dart';
import 'screens/results_screen.dart';
import 'screens/history_screen.dart';
import 'screens/profile_screen.dart';
import 'models/user.dart';
import 'models/scan_result.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );

  runApp(const SafePoseApp());
}

class SafePoseApp extends StatelessWidget {
  const SafePoseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SafePose',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const TestNavigator(), // Changed for testing
    );
  }
}

// ==========================================
// TEST NAVIGATOR - Remove this in production
// ==========================================
class TestNavigator extends StatelessWidget {
  const TestNavigator({super.key});

  @override
  Widget build(BuildContext context) {
    // Fake user for testing
    final fakeUser = User(
      name: 'Test User',
      email: 'test@example.com',
      token: 'fake_token',
    );

    // Fake result for testing
    final fakeResult = ScanResult(
      scanId: 'test123',
      prediction: 'none',
      confidence: 0.87,
      probabilities: {
        'none': 0.87,
        'stimulant': 0.05,
        'depressant': 0.05,
        'cannabis': 0.03,
      },
      indicators: [
        'Normal movement patterns',
        'Stable posture',
        'Consistent timing',
      ],
      detectionRate: 0.98,
      framesAnalyzed: 300,
      duration: 10.0,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('🧪 Test Navigator'),
        backgroundColor: AppTheme.cardColor,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Tap any screen to preview:',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 16),
          
          _buildNavButton(
            context,
            '1. Splash Screen',
            Icons.flash_on,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const SplashScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '2. Welcome Screen',
            Icons.waving_hand,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const WelcomeScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '3. Login Screen',
            Icons.login,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const LoginScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '4. Signup Screen',
            Icons.person_add,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const SignupScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '5. Home Screen',
            Icons.home,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => HomeScreen(user: fakeUser),
            )),
          ),
          
          _buildNavButton(
            context,
            '6. Scan Instructions',
            Icons.checklist,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const ScanInstructionsScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '7. Camera Screen',
            Icons.camera_alt,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const CameraScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '8. Results Screen (Normal)',
            Icons.check_circle,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => ResultsScreen(result: fakeResult),
            )),
          ),
          
          _buildNavButton(
            context,
            '9. Results Screen (Flagged)',
            Icons.warning,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => ResultsScreen(
                result: ScanResult(
                  scanId: 'test456',
                  prediction: 'depressant',
                  confidence: 0.73,
                  probabilities: {
                    'none': 0.12,
                    'stimulant': 0.08,
                    'depressant': 0.73,
                    'cannabis': 0.07,
                  },
                  indicators: [
                    'Reduced movement velocity',
                    'Increased postural sway',
                    'Slower reaction patterns',
                  ],
                  detectionRate: 0.95,
                  framesAnalyzed: 285,
                  duration: 10.0,
                ),
              ),
            )),
          ),
          
          _buildNavButton(
            context,
            '10. History Screen',
            Icons.history,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => const HistoryScreen(),
            )),
          ),
          
          _buildNavButton(
            context,
            '11. Profile Screen',
            Icons.person,
            () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => ProfileScreen(user: fakeUser),
            )),
          ),
        ],
      ),
    );
  }

  Widget _buildNavButton(
    BuildContext context,
    String title,
    IconData icon,
    VoidCallback onTap,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.cardColor,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.all(16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.primaryColor),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(fontSize: 16),
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 16),
          ],
        ),
      ),
    );
  }
}
