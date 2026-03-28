import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../models/scan_result.dart';
import 'results_screen.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => InsightsScreenState();
}

class InsightsScreenState extends State<InsightsScreen> {
  Map<String, dynamic>? _stats;
  List<ScanResult> _scans = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void refreshData() => _loadData();

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final stats = await ApiService().getStats();
      final scans = await ApiService().getHistory();
      if (mounted) {
        setState(() {
          _stats = stats;
          _scans = scans;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  int get _totalScans => _stats?['total_scans'] ?? 0;

  Map<String, dynamic> get _byPrediction {
    final raw = _stats?['by_prediction'];
    if (raw == null) return {};
    return Map<String, dynamic>.from(raw as Map);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: _isLoading
              ? const Center(
                  child: CircularProgressIndicator(color: AppTheme.primaryColor),
                )
              : SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header
                      Text(
                        'Insights',
                        style: Theme.of(context).textTheme.displayMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Your scan analytics at a glance',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppTheme.textSecondary,
                            ),
                      ),
                      const SizedBox(height: 24),

                      // 30-Day Trend
                      _buildTrendCard(context),
                      const SizedBox(height: 16),

                      // Category Breakdown
                      _buildCategoryBreakdown(context),
                      const SizedBox(height: 16),

                      // Scan Comparison
                      if (_scans.length >= 2) ...[
                        _buildScanComparison(context),
                        const SizedBox(height: 16),
                      ],

                      // Scan Quality Averages
                      _buildScanQuality(context),
                      const SizedBox(height: 16),

                      // Tip of the Day
                      _buildTipCard(context),
                      const SizedBox(height: 32),
                    ],
                  ),
                ),
        ),
      ),
    );
  }

  // ==========================================
  // 30-DAY TREND
  // ==========================================
  Widget _buildTrendCard(BuildContext context) {
    // Group scans into last 30 days by week
    final now = DateTime.now();
    final last30 = _scans.where((s) {
      if (s.timestamp == null) return false;
      return now.difference(s.timestamp!).inDays <= 30;
    }).toList();

    final normalCount = last30.where((s) => s.isNormal).length;
    final flaggedCount = last30.where((s) => !s.isNormal).length;

    // Build weekly data for chart
    List<_WeekData> weeklyData = [];
    for (int i = 3; i >= 0; i--) {
      final weekStart = now.subtract(Duration(days: (i + 1) * 7));
      final weekEnd = now.subtract(Duration(days: i * 7));
      final weekScans = last30.where((s) {
        if (s.timestamp == null) return false;
        return s.timestamp!.isAfter(weekStart) && s.timestamp!.isBefore(weekEnd);
      }).toList();
      final weekLabel = i == 0 ? 'This Week' : i == 1 ? 'Last Week' : '${i + 1}w ago';
      weeklyData.add(_WeekData(
        label: weekLabel,
        total: weekScans.length,
        normal: weekScans.where((s) => s.isNormal).length,
        flagged: weekScans.where((s) => !s.isNormal).length,
      ));
    }

    final maxScans = weeklyData.map((w) => w.total).fold(0, (a, b) => a > b ? a : b);

    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, '30-Day Trend', Icons.trending_up),
          const SizedBox(height: 8),

          // Stats summary
          Row(
            children: [
              _buildMiniStat('$normalCount', 'Normal', AppTheme.successColor),
              const SizedBox(width: 24),
              _buildMiniStat('$flaggedCount', 'Flagged', AppTheme.warningColor),
              const SizedBox(width: 24),
              _buildMiniStat('${last30.length}', 'Total', AppTheme.primaryColor),
            ],
          ),
          const SizedBox(height: 20),

          // Bar chart
          SizedBox(
            height: 140,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: weeklyData.map((week) {
                final height = maxScans > 0 ? (week.total / maxScans) * 90 : 0.0;
                return Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Text(
                        '${week.total}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        width: 32,
                        height: height.clamp(4.0, 90.0),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.bottomCenter,
                            end: Alignment.topCenter,
                            colors: [
                              AppTheme.primaryColor.withOpacity(0.3),
                              AppTheme.primaryColor,
                            ],
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        week.label,
                        style: TextStyle(fontSize: 9, color: AppTheme.textTertiary),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniStat(String value, String label, Color color) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            Text(
              label,
              style: TextStyle(fontSize: 11, color: AppTheme.textTertiary),
            ),
          ],
        ),
      ],
    );
  }

  // ==========================================
  // CATEGORY BREAKDOWN
  // ==========================================
  Widget _buildCategoryBreakdown(BuildContext context) {
    final categories = [
      _CategoryData('Normal', _byPrediction['none'] ?? 0, AppTheme.normalColor, '🟢'),
      _CategoryData('Stimulant', _byPrediction['stimulant'] ?? 0, AppTheme.stimulantColor, '⚡'),
      _CategoryData('Depressant', _byPrediction['depressant'] ?? 0, AppTheme.depressantColor, '😴'),
      _CategoryData('Cannabis', _byPrediction['cannabis'] ?? 0, AppTheme.cannabisColor, '🌿'),
    ];

    final maxCount = categories.map((c) => c.count).fold(0, (int a, int b) => a > b ? a : b);

    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Category Breakdown', Icons.bar_chart),
          const SizedBox(height: 16),

          ...categories.map((cat) {
            final fraction = maxCount > 0 ? cat.count / maxCount : 0.0;
            return Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Row(
                children: [
                  Text(cat.emoji, style: const TextStyle(fontSize: 18)),
                  const SizedBox(width: 10),
                  SizedBox(
                    width: 75,
                    child: Text(
                      cat.label,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: fraction,
                        backgroundColor: AppTheme.dividerColor,
                        valueColor: AlwaysStoppedAnimation<Color>(cat.color),
                        minHeight: 10,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  SizedBox(
                    width: 30,
                    child: Text(
                      '${cat.count}',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: cat.color,
                      ),
                      textAlign: TextAlign.right,
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
  // SCAN COMPARISON
  // ==========================================
  Widget _buildScanComparison(BuildContext context) {
    final sorted = List<ScanResult>.from(_scans);
    sorted.sort((a, b) => (b.timestamp ?? DateTime.now()).compareTo(a.timestamp ?? DateTime.now()));

    final latest = sorted[0];
    final previous = sorted[1];

    final confDiff = ((latest.confidence - previous.confidence) * 100).round();
    final confArrow = confDiff >= 0 ? '↑' : '↓';
    final confColor = confDiff >= 0 ? AppTheme.successColor : AppTheme.errorColor;

    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Scan Comparison', Icons.compare_arrows),
          const SizedBox(height: 16),

          Row(
            children: [
              // Previous
              Expanded(
                child: _buildComparisonBox(
                  context,
                  'Previous',
                  previous,
                  AppTheme.textTertiary,
                ),
              ),
              const SizedBox(width: 12),

              // Arrow
              Column(
                children: [
                  Icon(Icons.arrow_forward, color: AppTheme.primaryColor, size: 20),
                  const SizedBox(height: 4),
                  Text(
                    '$confArrow${confDiff.abs()}%',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: confColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 12),

              // Latest
              Expanded(
                child: _buildComparisonBox(
                  context,
                  'Latest',
                  latest,
                  AppTheme.primaryColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonBox(
    BuildContext context,
    String label,
    ScanResult scan,
    Color borderColor,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: AppTheme.textTertiary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            scan.predictionEmoji,
            style: const TextStyle(fontSize: 28),
          ),
          const SizedBox(height: 4),
          Text(
            scan.predictionLabel,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '${(scan.confidence * 100).toInt()}%',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: scan.isNormal ? AppTheme.successColor : AppTheme.warningColor,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // SCAN QUALITY AVERAGES
  // ==========================================
  Widget _buildScanQuality(BuildContext context) {
    double avgConfidence = 0;
    double avgDuration = 0;
    double avgDetectionRate = 0;

    if (_scans.isNotEmpty) {
      avgConfidence = _scans.map((s) => s.confidence).reduce((a, b) => a + b) / _scans.length;
      avgDuration = _scans.map((s) => s.duration).reduce((a, b) => a + b) / _scans.length;
      avgDetectionRate = _scans.map((s) => s.detectionRate).reduce((a, b) => a + b) / _scans.length;
    }

    return _buildCard(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(context, 'Average Scan Quality', Icons.verified),
          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildQualityMetric(
                  '${(avgConfidence * 100).toInt()}%',
                  'Avg Confidence',
                  Icons.psychology,
                  _getConfidenceColor(avgConfidence),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildQualityMetric(
                  '${avgDuration.toStringAsFixed(1)}s',
                  'Avg Duration',
                  Icons.timer,
                  AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildQualityMetric(
                  '${(avgDetectionRate * 100).toInt()}%',
                  'Detection',
                  Icons.person_search,
                  AppTheme.infoColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQualityMetric(
    String value,
    String label,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Icon(icon, size: 22, color: color),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(fontSize: 10, color: AppTheme.textTertiary),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // ==========================================
  // TIP CARD
  // ==========================================
  Widget _buildTipCard(BuildContext context) {
    final tips = [
      'For best results, scan in natural daylight with your full body visible.',
      'Stand 2-3 meters from the camera for the most accurate pose detection.',
      'Try scanning at different times of day to establish baseline patterns.',
      'Avoid loose clothing for more precise body movement analysis.',
      'A stable phone mount produces more consistent scan results.',
    ];

    final todayIndex = DateTime.now().day % tips.length;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryColor.withOpacity(0.08),
            AppTheme.primaryColor.withOpacity(0.03),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primaryColor.withOpacity(0.15)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.lightbulb_outline,
              color: AppTheme.primaryColor,
              size: 22,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Tip of the Day',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  tips[todayIndex],
                  style: TextStyle(
                    fontSize: 13,
                    color: AppTheme.textSecondary,
                    height: 1.4,
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
  // HELPERS
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

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.85) return AppTheme.successColor;
    if (confidence >= 0.70) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }
}

// Helper classes
class _WeekData {
  final String label;
  final int total;
  final int normal;
  final int flagged;

  _WeekData({
    required this.label,
    required this.total,
    required this.normal,
    required this.flagged,
  });
}

class _CategoryData {
  final String label;
  final int count;
  final Color color;
  final String emoji;

  _CategoryData(this.label, this.count, this.color, this.emoji);
}
