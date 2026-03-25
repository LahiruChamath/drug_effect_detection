import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/user.dart';
import '../models/scan_result.dart';
import '../services/api_service.dart';
import 'scan_instructions_screen.dart';
import 'results_screen.dart';

class HomeScreen extends StatefulWidget {
  final User user;

  const HomeScreen({super.key, required this.user});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _stats;
  List<ScanResult> _recentScans = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final stats = await ApiService().getStats();
      final scans = await ApiService().getHistory();
      if (mounted) {
        setState(() {
          _stats = stats;
          _recentScans = scans;
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
      backgroundColor: Colors.white,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ==========================================
                // HEADER (greeting + notification bell)
                // ==========================================
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Hello, ${widget.user.name.split(' ').first} 👋',
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Ready for a scan?',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppTheme.textSecondary,
                              ),
                        ),
                      ],
                    ),
                    GestureDetector(
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: const Text('No new notifications'),
                            behavior: SnackBarBehavior.floating,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        );
                      },
                      child: Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: AppTheme.primaryColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Icon(
                          Icons.notifications_outlined,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // ==========================================
                // STATS CARD (Total Scans + Normal)
                // ==========================================
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: _isLoading
                      ? const Center(
                          child: Padding(
                            padding: EdgeInsets.all(20),
                            child: CircularProgressIndicator(
                              color: AppTheme.primaryColor,
                            ),
                          ),
                        )
                      : Row(
                          children: [
                            Expanded(
                              child: _buildStatItem(
                                context,
                                '$_totalScans',
                                'Total Scans',
                                Icons.analytics_outlined,
                              ),
                            ),
                            Container(
                              width: 1,
                              height: 50,
                              color: AppTheme.borderColor,
                            ),
                            Expanded(
                              child: _buildStatItem(
                                context,
                                '${_byPrediction['none'] ?? 0}',
                                'Normal',
                                Icons.check_circle_outline,
                              ),
                            ),
                          ],
                        ),
                ),
                const SizedBox(height: 24),

                // ==========================================
                // START SCAN CARD
                // ==========================================
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        AppTheme.primaryColor,
                        AppTheme.primaryColor.withOpacity(0.8),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.primaryColor.withOpacity(0.3),
                        blurRadius: 20,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.play_arrow_rounded,
                          size: 50,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'Start New Scan',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Tap to begin 10-second analysis',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.white.withOpacity(0.8),
                        ),
                      ),
                      const SizedBox(height: 32),
                      SizedBox(
                        width: double.infinity,
                        height: 56,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => const ScanInstructionsScreen(),
                              ),
                            ).then((_) => _loadData());
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: AppTheme.primaryColor,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          child: const Text(
                            'Begin Scan',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // ==========================================
                // WEEKLY ACTIVITY CHART (NEW)
                // ==========================================
                if (!_isLoading) ...[
                  _buildWeeklyChart(context),
                  const SizedBox(height: 24),
                ],

                // ==========================================
                // LAST SCAN QUICK GLANCE (NEW)
                // ==========================================
                if (!_isLoading && _recentScans.isNotEmpty) ...[
                  _buildLastScanCard(context),
                  const SizedBox(height: 24),
                ],

                // ==========================================
                // PREDICTION BREAKDOWN (KEEP)
                // ==========================================
                if (!_isLoading && _byPrediction.isNotEmpty) ...[
                  Text(
                    'Prediction Breakdown',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 16),
                  _buildPredictionBreakdown(),
                  const SizedBox(height: 24),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ==========================================
  // WEEKLY ACTIVITY CHART
  // ==========================================
  Widget _buildWeeklyChart(BuildContext context) {
    final now = DateTime.now();
    final dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Count scans per day of this week
    // Normalize to midnight to avoid time-of-day offset issues
    final startOfWeekDate = DateTime(now.year, now.month, now.day).subtract(Duration(days: now.weekday - 1));
    List<int> dayCounts = List.filled(7, 0);

    for (final scan in _recentScans) {
      if (scan.timestamp == null) continue;
      final scanDate = DateTime(scan.timestamp!.year, scan.timestamp!.month, scan.timestamp!.day);
      final diff = scanDate.difference(startOfWeekDate).inDays;
      if (diff >= 0 && diff < 7) {
        dayCounts[diff]++;
      }
    }

    final maxCount = dayCounts.reduce((a, b) => a > b ? a : b);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.show_chart, size: 20, color: AppTheme.primaryColor),
              const SizedBox(width: 10),
              Text(
                'Weekly Activity',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(7, (i) {
                final isToday = i == now.weekday - 1;
                final height = maxCount > 0
                    ? (dayCounts[i] / maxCount) * 70
                    : 0.0;

                return Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      if (dayCounts[i] > 0)
                        Text(
                          '${dayCounts[i]}',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isToday
                                ? AppTheme.primaryColor
                                : AppTheme.textTertiary,
                          ),
                        ),
                      const SizedBox(height: 4),
                      Container(
                        width: 24,
                        height: height.clamp(4.0, 70.0),
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        decoration: BoxDecoration(
                          color: isToday
                              ? AppTheme.primaryColor
                              : dayCounts[i] > 0
                                  ? AppTheme.primaryColor.withOpacity(0.3)
                                  : AppTheme.dividerColor,
                          borderRadius: BorderRadius.circular(6),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        dayLabels[i],
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                          color: isToday
                              ? AppTheme.primaryColor
                              : AppTheme.textTertiary,
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // LAST SCAN QUICK GLANCE
  // ==========================================
  Widget _buildLastScanCard(BuildContext context) {
    // Sort to get latest
    final sorted = List<ScanResult>.from(_recentScans);
    sorted.sort((a, b) =>
        (b.timestamp ?? DateTime.now()).compareTo(a.timestamp ?? DateTime.now()));
    final lastScan = sorted.first;

    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ResultsScreen(result: lastScan),
          ),
        );
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: AppTheme.cardShadow,
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: (lastScan.isNormal
                        ? AppTheme.successColor
                        : AppTheme.warningColor)
                    .withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  lastScan.predictionEmoji,
                  style: const TextStyle(fontSize: 26),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.history, size: 14, color: AppTheme.textTertiary),
                      const SizedBox(width: 4),
                      Text(
                        'Last Scan',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppTheme.textTertiary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${lastScan.predictionLabel} · ${(lastScan.confidence * 100).toInt()}%',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (lastScan.timestamp != null)
                    Text(
                      _formatDate(lastScan.timestamp!),
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.textTertiary,
                      ),
                    ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.primaryLight,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'View',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryColor,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================
  // PREDICTION BREAKDOWN (existing, kept)
  // ==========================================
  Widget _buildPredictionBreakdown() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: _byPrediction.entries.map((entry) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              children: [
                _getPredictionIcon(entry.key),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _getPredictionLabel(entry.key),
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getPredictionColor(entry.key).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${entry.value}',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _getPredictionColor(entry.key),
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ==========================================
  // HELPER WIDGETS
  // ==========================================
  Widget _buildStatItem(
    BuildContext context,
    String value,
    String label,
    IconData icon,
  ) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: AppTheme.primaryColor, size: 20),
            const SizedBox(width: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
        ),
      ],
    );
  }

  Widget _getPredictionIcon(String prediction) {
    IconData icon;
    Color color;

    switch (prediction.toLowerCase()) {
      case 'none':
        icon = Icons.check_circle;
        color = AppTheme.successColor;
        break;
      case 'stimulant':
        icon = Icons.flash_on;
        color = AppTheme.warningColor;
        break;
      case 'depressant':
        icon = Icons.arrow_downward;
        color = AppTheme.errorColor;
        break;
      case 'cannabis':
        icon = Icons.grass;
        color = Colors.amber;
        break;
      default:
        icon = Icons.help;
        color = AppTheme.textSecondary;
    }

    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, color: color, size: 20),
    );
  }

  String _getPredictionLabel(String prediction) {
    switch (prediction.toLowerCase()) {
      case 'none':
        return 'Normal';
      case 'stimulant':
        return 'Stimulant';
      case 'depressant':
        return 'Depressant';
      case 'cannabis':
        return 'Cannabis';
      default:
        return prediction;
    }
  }

  Color _getPredictionColor(String prediction) {
    switch (prediction.toLowerCase()) {
      case 'none':
        return AppTheme.successColor;
      case 'stimulant':
        return AppTheme.warningColor;
      case 'depressant':
        return AppTheme.errorColor;
      case 'cannabis':
        return Colors.amber;
      default:
        return AppTheme.textSecondary;
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final scanDate = DateTime(date.year, date.month, date.day);

    String timeStr =
        '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

    if (scanDate == today) {
      return 'Today, $timeStr';
    } else if (scanDate == yesterday) {
      return 'Yesterday, $timeStr';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }
}
