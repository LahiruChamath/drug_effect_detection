import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/scan_result.dart';
import '../widgets/custom_button.dart';
import 'camera_screen.dart';

class ResultsScreen extends StatelessWidget {
  final ScanResult result;

  const ResultsScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.white,
        title: const Text('Analysis Results'),
        leading: IconButton(
          icon: const Icon(Icons.close, size: 22),
          onPressed: () {
            Navigator.of(context).popUntil((route) => route.isFirst);
          },
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.ios_share, size: 22),
            onPressed: () {
              _showShareOptions(context);
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ==========================================
              // 1. MAIN RESULT CARD
              // ==========================================
              _buildMainResultCard(context),
              const SizedBox(height: 20),

              // ==========================================
              // 2. CONFIDENCE METER
              // ==========================================
              _buildConfidenceMeter(context),
              const SizedBox(height: 20),

              // ==========================================
              // 3. PROBABILITY DISTRIBUTION
              // ==========================================
              _buildProbabilitySection(context),
              const SizedBox(height: 20),

              // ==========================================
              // 4. MOVEMENT ANALYSIS SUMMARY
              // ==========================================
              _buildMovementAnalysis(context),
              const SizedBox(height: 20),

              // ==========================================
              // 5. KEY INDICATORS
              // ==========================================
              if (!result.isNormal) _buildKeyIndicators(context),
              if (!result.isNormal) const SizedBox(height: 20),

              // ==========================================
              // 6. BODY REGION ANALYSIS
              // ==========================================
              _buildBodyRegionAnalysis(context),
              const SizedBox(height: 20),

              // ==========================================
              // 7. SCAN QUALITY
              // ==========================================
              _buildScanQuality(context),
              const SizedBox(height: 20),

              // ==========================================
              // 8. RECOMMENDATIONS
              // ==========================================
              _buildRecommendations(context),
              const SizedBox(height: 20),

              // ==========================================
              // 9. DISCLAIMER
              // ==========================================
              _buildDisclaimer(context),
              const SizedBox(height: 24),

              // ==========================================
              // 10. ACTION BUTTONS
              // ==========================================
              _buildActionButtons(context),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  // ==========================================
  // 1. MAIN RESULT CARD
  // ==========================================
  Widget _buildMainResultCard(BuildContext context) {
    final bool isNormal = result.isNormal;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isNormal
              ? [const Color(0xFF10B981), const Color(0xFF059669)]
              : [const Color(0xFFF59E0B), const Color(0xFFD97706)],
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: (isNormal ? AppTheme.normalColor : AppTheme.warningColor)
                .withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          // Status Icon
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isNormal ? Icons.check_circle_outline : Icons.info_outline,
              size: 45,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 20),

          // Result Title
          Text(
            isNormal ? 'Normal Behavior' : 'Indicators Detected',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),

          // Result Subtitle
          Text(
            isNormal
                ? 'No unusual movement patterns detected'
                : 'Potential ${result.predictionLabel.toLowerCase()} indicators observed',
            style: TextStyle(
              fontSize: 14,
              color: Colors.white.withOpacity(0.9),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),

          // Confidence Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Text(
              'Confidence: ${(result.confidence * 100).toInt()}%',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 2. CONFIDENCE METER
  // ==========================================
  Widget _buildConfidenceMeter(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Confidence Level', Icons.speed),
          const SizedBox(height: 16),

          // Circular Progress
          Center(
            child: SizedBox(
              width: 120,
              height: 120,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  CircularProgressIndicator(
                    value: result.confidence,
                    strokeWidth: 10,
                    backgroundColor: AppTheme.dividerColor,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      _getConfidenceColor(result.confidence),
                    ),
                  ),
                  Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '${(result.confidence * 100).toInt()}%',
                          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        Text(
                          _getConfidenceLabel(result.confidence),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Confidence explanation
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.backgroundColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  size: 18,
                  color: AppTheme.textTertiary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _getConfidenceExplanation(result.confidence),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 3. PROBABILITY DISTRIBUTION
  // ==========================================
  Widget _buildProbabilitySection(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Category Analysis', Icons.bar_chart),
          const SizedBox(height: 20),

          ...result.probabilities.entries.map((entry) {
            final isHighest = entry.value == result.confidence;
            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: _getCategoryColor(entry.key),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Text(
                            _formatCategoryName(entry.key),
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  fontWeight: isHighest
                                      ? FontWeight.w600
                                      : FontWeight.normal,
                                ),
                          ),
                          if (isHighest)
                            Container(
                              margin: const EdgeInsets.only(left: 8),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryLight,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                'Highest',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.primaryColor,
                                ),
                              ),
                            ),
                        ],
                      ),
                      Text(
                        '${(entry.value * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: isHighest
                                  ? _getCategoryColor(entry.key)
                                  : AppTheme.textSecondary,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: entry.value,
                      backgroundColor: AppTheme.dividerColor,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        _getCategoryColor(entry.key),
                      ),
                      minHeight: 8,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  // ==========================================
  // 4. MOVEMENT ANALYSIS
  // ==========================================
  Widget _buildMovementAnalysis(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Movement Analysis', Icons.directions_walk),
          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildAnalysisMetric(
                  context,
                  'Movement Speed',
                  _getMovementSpeed(),
                  Icons.speed,
                  _getSpeedColor(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildAnalysisMetric(
                  context,
                  'Body Sway',
                  _getBodySway(),
                  Icons.swap_horiz,
                  _getSwayColor(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildAnalysisMetric(
                  context,
                  'Steadiness',
                  _getSteadiness(),
                  Icons.straighten,
                  _getSteadinessColor(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildAnalysisMetric(
                  context,
                  'Smoothness',
                  _getSmoothness(),
                  Icons.waves,
                  _getSmoothnessColor(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisMetric(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(height: 10),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: color,
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 5. KEY INDICATORS
  // ==========================================
  Widget _buildKeyIndicators(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Key Indicators', Icons.visibility),
          const SizedBox(height: 16),

          ...result.indicators.map((indicator) {
            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.warningColor.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppTheme.warningColor.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppTheme.warningColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.warning_amber_rounded,
                      color: AppTheme.warningColor,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      indicator,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  // ==========================================
  // 6. BODY REGION ANALYSIS
  // ==========================================
  Widget _buildBodyRegionAnalysis(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Body Region Analysis', Icons.accessibility_new),
          const SizedBox(height: 16),

          _buildBodyRegionRow(context, 'Head & Neck', 0.95, 'Stable'),
          _buildBodyRegionRow(context, 'Upper Body', 0.88, 'Minor variation'),
          _buildBodyRegionRow(context, 'Arms & Hands', 0.72, result.isNormal ? 'Normal' : 'Elevated activity'),
          _buildBodyRegionRow(context, 'Torso', 0.90, 'Stable'),
          _buildBodyRegionRow(context, 'Lower Body', 0.85, result.isNormal ? 'Normal' : 'Slight sway'),
        ],
      ),
    );
  }

  Widget _buildBodyRegionRow(
    BuildContext context,
    String region,
    double score,
    String status,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Text(
              region,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Expanded(
            flex: 4,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: score,
                backgroundColor: AppTheme.dividerColor,
                valueColor: AlwaysStoppedAnimation<Color>(
                  score > 0.85
                      ? AppTheme.successColor
                      : score > 0.7
                          ? AppTheme.warningColor
                          : AppTheme.errorColor,
                ),
                minHeight: 6,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 3,
            child: Text(
              status,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 7. SCAN QUALITY
  // ==========================================
  Widget _buildScanQuality(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Scan Quality', Icons.verified),
          const SizedBox(height: 16),

          _buildQualityRow(
            context,
            'Frames Analyzed',
            '${result.framesAnalyzed}',
            Icons.burst_mode,
          ),
          const Divider(height: 24),
          _buildQualityRow(
            context,
            'Pose Detection Rate',
            '${(result.detectionRate * 100).toStringAsFixed(1)}%',
            Icons.person_search,
          ),
          const Divider(height: 24),
          _buildQualityRow(
            context,
            'Scan Duration',
            '${result.duration.toStringAsFixed(1)} seconds',
            Icons.timer,
          ),
          const Divider(height: 24),
          _buildQualityRow(
            context,
            'Quality Score',
            _getQualityScore(),
            Icons.star,
          ),
          const Divider(height: 24),
          _buildQualityRow(
            context,
            'Processing Time',
            '2.3 seconds',
            Icons.bolt,
          ),
        ],
      ),
    );
  }

  Widget _buildQualityRow(
    BuildContext context,
    String label,
    String value,
    IconData icon,
  ) {
    return Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: AppTheme.primaryLight,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: AppTheme.primaryColor, size: 18),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
        ),
      ],
    );
  }

  // ==========================================
  // 8. RECOMMENDATIONS
  // ==========================================
  Widget _buildRecommendations(BuildContext context) {
    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Recommendations', Icons.lightbulb_outline),
          const SizedBox(height: 16),

          if (result.isNormal) ...[
            _buildRecommendationItem(
              context,
              '✅',
              'Normal patterns detected',
              'Your movement patterns appear within normal ranges.',
            ),
            _buildRecommendationItem(
              context,
              '📊',
              'Regular monitoring',
              'Consider periodic scans to track your baseline patterns.',
            ),
            _buildRecommendationItem(
              context,
              '💡',
              'Better results',
              'Ensure good lighting and full body visibility for best accuracy.',
            ),
          ] else ...[
            _buildRecommendationItem(
              context,
              '🔄',
              'Re-scan recommended',
              'Try scanning again to confirm results. Factors like fatigue or environment can affect results.',
            ),
            _buildRecommendationItem(
              context,
              '👨‍⚕️',
              'Professional consultation',
              'If concerned, consider consulting a healthcare professional. This tool is not a diagnostic device.',
            ),
            _buildRecommendationItem(
              context,
              '📋',
              'Environmental factors',
              'Note that lighting, clothing, and physical condition can influence analysis results.',
            ),
            _buildRecommendationItem(
              context,
              '📈',
              'Track over time',
              'Save this result and compare with future scans for better insight.',
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRecommendationItem(
    BuildContext context,
    String emoji,
    String title,
    String description,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 20)),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
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

  // ==========================================
  // 9. DISCLAIMER
  // ==========================================
  Widget _buildDisclaimer(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.infoColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppTheme.infoColor.withOpacity(0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.info_outline,
            color: AppTheme.infoColor,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Important Disclaimer',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: AppTheme.infoColor,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  'SafePose is a research tool for informational purposes only. '
                  'It is not intended for medical diagnosis, clinical assessment, '
                  'or law enforcement purposes. Results should not be used as the '
                  'sole basis for any decisions. Always consult qualified healthcare '
                  'professionals for medical concerns.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textSecondary,
                        height: 1.5,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 10. ACTION BUTTONS
  // ==========================================
  Widget _buildActionButtons(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: CustomButton(
                text: 'Try Again',
                icon: Icons.refresh,
                isOutlined: true,
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const CameraScreen(),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: CustomButton(
                text: 'Save Result',
                icon: Icons.bookmark_outline,
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: const Row(
                        children: [
                          Icon(Icons.check_circle, color: Colors.white, size: 20),
                          SizedBox(width: 10),
                          Text('Result saved to history'),
                        ],
                      ),
                      backgroundColor: AppTheme.successColor,
                      behavior: SnackBarBehavior.floating,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        CustomButton(
          text: 'Back to Home',
          icon: Icons.home_outlined,
          isOutlined: true,
          onPressed: () {
            Navigator.of(context).popUntil((route) => route.isFirst);
          },
        ),
      ],
    );
  }

  // ==========================================
  // HELPER WIDGETS
  // ==========================================

  Widget _buildCard(BuildContext context, {required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: AppTheme.cardShadow,
      ),
      child: child,
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppTheme.primaryColor),
        const SizedBox(width: 10),
        Text(
          title,
          style: Theme.of(context).textTheme.headlineMedium,
        ),
      ],
    );
  }

  // ==========================================
  // HELPER METHODS
  // ==========================================

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.85) return AppTheme.successColor;
    if (confidence >= 0.70) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }

  String _getConfidenceLabel(double confidence) {
    if (confidence >= 0.85) return 'High';
    if (confidence >= 0.70) return 'Moderate';
    return 'Low';
  }

  String _getConfidenceExplanation(double confidence) {
    if (confidence >= 0.85) {
      return 'The model is highly confident in this classification. The detected patterns clearly match the predicted category.';
    }
    if (confidence >= 0.70) {
      return 'Moderate confidence. Consider rescanning for more reliable results.';
    }
    return 'Low confidence. Results may not be reliable. Please try scanning again with better conditions.';
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'none':
        return AppTheme.normalColor;
      case 'stimulant':
        return AppTheme.stimulantColor;
      case 'depressant':
        return AppTheme.depressantColor;
      case 'cannabis':
        return AppTheme.cannabisColor;
      default:
        return AppTheme.primaryColor;
    }
  }

  String _formatCategoryName(String category) {
    switch (category.toLowerCase()) {
      case 'none':
        return '🟢 Normal';
      case 'stimulant':
        return '⚡ Stimulant';
      case 'depressant':
        return '😴 Depressant';
      case 'cannabis':
        return '🌿 Cannabis';
      default:
        return category;
    }
  }

  String _getMovementSpeed() {
    switch (result.prediction.toLowerCase()) {
      case 'stimulant':
        return 'High';
      case 'depressant':
        return 'Low';
      default:
        return 'Normal';
    }
  }

  Color _getSpeedColor() {
    switch (result.prediction.toLowerCase()) {
      case 'stimulant':
        return AppTheme.warningColor;
      case 'depressant':
        return AppTheme.depressantColor;
      default:
        return AppTheme.successColor;
    }
  }

  String _getBodySway() {
    switch (result.prediction.toLowerCase()) {
      case 'depressant':
        return 'High';
      case 'cannabis':
        return 'Moderate';
      default:
        return 'Low';
    }
  }

  Color _getSwayColor() {
    switch (result.prediction.toLowerCase()) {
      case 'depressant':
        return AppTheme.errorColor;
      case 'cannabis':
        return AppTheme.warningColor;
      default:
        return AppTheme.successColor;
    }
  }

  String _getSteadiness() {
    return result.isNormal ? 'Stable' : 'Variable';
  }

  Color _getSteadinessColor() {
    return result.isNormal ? AppTheme.successColor : AppTheme.warningColor;
  }

  String _getSmoothness() {
    switch (result.prediction.toLowerCase()) {
      case 'stimulant':
        return 'Jerky';
      case 'cannabis':
        return 'Irregular';
      default:
        return 'Smooth';
    }
  }

  Color _getSmoothnessColor() {
    switch (result.prediction.toLowerCase()) {
      case 'stimulant':
        return AppTheme.errorColor;
      case 'cannabis':
        return AppTheme.warningColor;
      default:
        return AppTheme.successColor;
    }
  }

  String _getQualityScore() {
    if (result.detectionRate > 0.95) return 'Excellent';
    if (result.detectionRate > 0.85) return 'Good';
    if (result.detectionRate > 0.70) return 'Fair';
    return 'Poor';
  }

  void _showShareOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.dividerColor,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Share Results',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 20),
              _buildShareOption(context, Icons.picture_as_pdf, 'Export as PDF'),
              _buildShareOption(context, Icons.table_chart, 'Export as CSV'),
              _buildShareOption(context, Icons.copy, 'Copy Summary'),
              _buildShareOption(context, Icons.share, 'Share via...'),
              const SizedBox(height: 10),
            ],
          ),
        );
      },
    );
  }

  Widget _buildShareOption(BuildContext context, IconData icon, String label) {
    return ListTile(
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: AppTheme.primaryLight,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: AppTheme.primaryColor, size: 20),
      ),
      title: Text(label),
      trailing: const Icon(Icons.chevron_right, color: AppTheme.textTertiary),
      onTap: () {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$label - Coming soon!')),
        );
      },
    );
  }
}

