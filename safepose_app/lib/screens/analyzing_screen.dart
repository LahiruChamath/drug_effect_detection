import 'dart:io';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../models/scan_result.dart';
import 'results_screen.dart';
import 'camera_screen.dart';

class AnalyzingScreen extends StatefulWidget {
  final String videoPath;

  const AnalyzingScreen({super.key, required this.videoPath});

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  int _currentStep = 0;
  String _statusText = 'Uploading video...';
  double _progress = 0.0;
  String? _errorMessage;

  final List<String> _steps = [
    'Uploading video...',
    'Extracting pose data...',
    'Analyzing movement...',
    'Generating results...',
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
    
    _startAnalysis();
  }

  Future<void> _startAnalysis() async {
    try {
      // Simulate progress through steps
      for (int i = 0; i < _steps.length - 1; i++) {
        await Future.delayed(const Duration(milliseconds: 800));
        if (mounted) {
          setState(() {
            _currentStep = i + 1;
            _statusText = _steps[i + 1];
            _progress = (i + 1) / _steps.length;
          });
        }
      }

      // Call API
      final videoFile = File(widget.videoPath);
      final result = await ApiService().analyzeVideo(videoFile);

      // Delete temp video
      if (await videoFile.exists()) {
        await videoFile.delete();
      }

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ResultsScreen(result: result),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
        });
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),
              
              // Animated Icon
              if (_errorMessage == null)
                AnimatedBuilder(
                  animation: _controller,
                  builder: (context, child) {
                    return Transform.rotate(
                      angle: _controller.value * 2 * 3.14159,
                      child: Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          color: AppTheme.primaryColor.withOpacity(0.1),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.psychology,
                          size: 50,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    );
                  },
                )
              else
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: AppTheme.errorColor.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.error_outline,
                    size: 50,
                    color: AppTheme.errorColor,
                  ),
                ),
              
              const SizedBox(height: 32),
              
              // Title
              Text(
                _errorMessage == null ? 'Analyzing...' : 'Analysis Failed',
                style: Theme.of(context).textTheme.displaySmall,
              ),
              const SizedBox(height: 32),
              
              // Steps
              if (_errorMessage == null)
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppTheme.cardColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: List.generate(_steps.length, (index) {
                      final isCompleted = index < _currentStep;
                      final isCurrent = index == _currentStep;
                      
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        child: Row(
                          children: [
                            Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: isCompleted
                                    ? AppTheme.primaryColor
                                    : isCurrent
                                        ? AppTheme.primaryColor.withOpacity(0.3)
                                        : AppTheme.surfaceColor,
                                shape: BoxShape.circle,
                              ),
                              child: isCompleted
                                  ? const Icon(
                                      Icons.check,
                                      size: 16,
                                      color: Colors.white,
                                    )
                                  : isCurrent
                                      ? const SizedBox(
                                          width: 12,
                                          height: 12,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            valueColor:
                                                AlwaysStoppedAnimation<Color>(
                                              AppTheme.primaryColor,
                                            ),
                                          ),
                                        )
                                      : null,
                            ),
                            const SizedBox(width: 12),
                            Text(
                              _steps[index],
                              style: TextStyle(
                                color: isCompleted || isCurrent
                                    ? Colors.white
                                    : AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppTheme.cardColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _errorMessage!,
                        style: const TextStyle(color: AppTheme.errorColor),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 20),
                      ElevatedButton(
                        onPressed: () {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const CameraScreen(),
                            ),
                          );
                        },
                        child: const Text('Try Again'),
                      ),
                    ],
                  ),
                ),
              
              const SizedBox(height: 32),
              
              // Progress Bar
              if (_errorMessage == null)
                Column(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: LinearProgressIndicator(
                        value: _progress,
                        backgroundColor: AppTheme.surfaceColor,
                        valueColor: const AlwaysStoppedAnimation<Color>(
                          AppTheme.primaryColor,
                        ),
                        minHeight: 8,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '${(_progress * 100).toInt()}%',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              
              const Spacer(),
              
              // Privacy Notice
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.lock,
                      color: AppTheme.primaryColor,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Your video is not stored. Only skeleton data is analyzed.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
