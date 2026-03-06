import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'results_screen.dart';

class AnalyzingScreen extends StatefulWidget {
  final String videoPath;
  final List<List<List<double>>>? poseFrames;

  const AnalyzingScreen({
    super.key,
    required this.videoPath,
    this.poseFrames,
  });

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  String _status = 'Initializing...';

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    _startAnalysis();
  }

  /// Generate realistic-looking dummy pose frames for web demo mode.
  /// Each frame = 33 landmarks × 4 values (x, y, z, visibility).
  List<List<List<double>>> _generateDummyFrames({int frameCount = 90}) {
    final rng = Random();
    return List.generate(frameCount, (_) {
      return List.generate(33, (landmarkIdx) {
        return [
          0.3 + rng.nextDouble() * 0.4,  // x  (0-1)
          0.2 + rng.nextDouble() * 0.6,  // y  (0-1)
          rng.nextDouble() * 0.1 - 0.05, // z
          0.8 + rng.nextDouble() * 0.2,  // visibility
        ];
      });
    });
  }

  Future<void> _startAnalysis() async {
    try {
      setState(() => _status = 'Processing video...');
      await Future.delayed(const Duration(milliseconds: 800));

      setState(() => _status = 'Extracting pose data...');
      await Future.delayed(const Duration(milliseconds: 800));

      setState(() => _status = 'Running AI analysis...');

      // Use real frames if provided (mobile), otherwise generate dummy frames (web)
      final frames = widget.poseFrames ?? _generateDummyFrames();

      // Call the real API
      final result = await ApiService().analyzePose(frames);

      setState(() => _status = 'Generating results...');
      await Future.delayed(const Duration(milliseconds: 400));

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ResultsScreen(result: result),
          ),
        );
      }
    } catch (e) {
      setState(() => _status = 'Analysis failed');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );

        await Future.delayed(const Duration(seconds: 2));
        if (mounted) Navigator.pop(context);
      }
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Animated icon
                RotationTransition(
                  turns: _animationController,
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [
                          AppTheme.primaryColor,
                          AppTheme.primaryColor.withOpacity(0.5),
                        ],
                      ),
                    ),
                    child: const Icon(
                      Icons.analytics,
                      size: 50,
                      color: Colors.white,
                    ),
                  ),
                ),

                const SizedBox(height: 40),

                Text(
                  _status,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 16),

                Text(
                  'Please wait while we analyze your scan...',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 40),

                const LinearProgressIndicator(
                  backgroundColor: AppTheme.borderColor,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    AppTheme.primaryColor,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
