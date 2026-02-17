import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/custom_button.dart';
import 'camera_screen.dart';

class ScanInstructionsScreen extends StatelessWidget {
  const ScanInstructionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New Scan'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const SizedBox(height: 20),
              
              // Icon
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.checklist,
                  size: 40,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(height: 24),
              
              // Title
              Text(
                'Before You Start',
                style: Theme.of(context).textTheme.displaySmall,
              ),
              const SizedBox(height: 32),
              
              // Instructions
              Expanded(
                child: ListView(
                  children: [
                    _buildInstructionCard(
                      context,
                      Icons.person_pin_circle,
                      'Position yourself',
                      'Stand 2-3 meters from the camera',
                    ),
                    const SizedBox(height: 16),
                    _buildInstructionCard(
                      context,
                      Icons.lightbulb_outline,
                      'Good lighting',
                      'Make sure you\'re well lit and visible',
                    ),
                    const SizedBox(height: 16),
                    _buildInstructionCard(
                      context,
                      Icons.accessibility_new,
                      'Full body visible',
                      'Your entire body should be in frame',
                    ),
                    const SizedBox(height: 16),
                    _buildInstructionCard(
                      context,
                      Icons.timer,
                      '10 seconds',
                      'Recording will last exactly 10 seconds',
                    ),
                    const SizedBox(height: 16),
                    _buildInstructionCard(
                      context,
                      Icons.pan_tool,
                      'Stay steady',
                      'Try to remain in the same position',
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Open Camera Button
              CustomButton(
                text: 'Open Camera',
                icon: Icons.camera_alt,
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const CameraScreen()),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInstructionCard(
    BuildContext context,
    IconData icon,
    String title,
    String description,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: AppTheme.primaryColor,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
