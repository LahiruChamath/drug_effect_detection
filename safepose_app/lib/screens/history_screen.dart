import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../models/scan_result.dart';
import 'results_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<ScanResult> _scans = [];
  bool _isLoading = true;
  String _filter = 'all';

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final scans = await ApiService().getHistory();
      if (mounted) {
        setState(() {
          _scans = scans;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _scans = [];
          _isLoading = false;
        });
      }
    }
  }

  Future<bool> _deleteScan(ScanResult scan) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Delete Scan'),
        content: const Text('Are you sure you want to delete this scan result? This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.errorColor),
            child: const Text('Delete', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await ApiService().deleteScan(scan.scanId);
        _loadHistory();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('Scan deleted successfully'),
              behavior: SnackBarBehavior.floating,
              backgroundColor: AppTheme.textPrimary,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
          );
        }
        return true;
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.errorColor),
          );
        }
        return false;
      }
    }
    return false;
  }

  List<ScanResult> get _filteredScans {
    final sorted = List<ScanResult>.from(_scans);
    sorted.sort((a, b) => (b.timestamp ?? DateTime.now()).compareTo(a.timestamp ?? DateTime.now()));
    
    switch (_filter) {
      case 'normal':
        return sorted.where((s) => s.isNormal).toList();
      case 'flagged':
        return sorted.where((s) => !s.isNormal).toList();
      default:
        return sorted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: CustomScrollView(
        slivers: [
          _buildSliverAppBar(),
          _buildFilterSection(),
          _buildScanList(),
        ],
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      expandedHeight: 120.0,
      floating: false,
      pinned: true,
      elevation: 0,
      backgroundColor: Colors.white,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new, size: 20, color: AppTheme.textPrimary),
        onPressed: () => Navigator.pop(context),
      ),
      flexibleSpace: FlexibleSpaceBar(
        titlePadding: const EdgeInsets.only(left: 60, bottom: 16),
        title: Text(
          'Scan History',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
        ),
        background: Container(color: Colors.white),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh, color: AppTheme.primaryColor),
          onPressed: _loadHistory,
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildFilterSection() {
    return SliverToBoxAdapter(
      child: Container(
        color: Colors.white,
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _buildFilterChip('All Scans', 'all'),
              const SizedBox(width: 8),
              _buildFilterChip('Normal', 'normal'),
              const SizedBox(width: 8),
              _buildFilterChip('Flagged', 'flagged'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScanList() {
    if (_isLoading) {
      return const SliverFillRemaining(
        child: Center(
          child: CircularProgressIndicator(color: AppTheme.primaryColor),
        ),
      );
    }

    if (_filteredScans.isEmpty) {
      return SliverFillRemaining(
        child: _buildEmptyState(),
      );
    }

    return SliverPadding(
      padding: const EdgeInsets.all(16),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            final scan = _filteredScans[index];
            return _buildScanItem(context, scan);
          },
          childCount: _filteredScans.length,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    String message;
    IconData icon;
    
    switch (_filter) {
      case 'normal':
        message = 'No normal scans found';
        icon = Icons.check_circle_outline;
        break;
      case 'flagged':
        message = 'No flagged scans found';
        icon = Icons.warning_amber_rounded;
        break;
      default:
        message = 'Your scan history is empty';
        icon = Icons.history;
    }

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              boxShadow: AppTheme.cardShadow,
            ),
            child: Icon(icon, size: 64, color: AppTheme.primaryColor.withOpacity(0.3)),
          ),
          const SizedBox(height: 24),
          Text(
            message,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Keep regular checkups for better tracking',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textSecondary,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, String value) {
    final isSelected = _filter == value;
    
    return GestureDetector(
      onTap: () => setState(() => _filter = value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryColor : AppTheme.backgroundColor,
          borderRadius: BorderRadius.circular(30),
          boxShadow: isSelected ? [
            BoxShadow(
              color: AppTheme.primaryColor.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            )
          ] : [],
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : AppTheme.textSecondary,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildScanItem(BuildContext context, ScanResult scan) {
    final Color statusColor = scan.isNormal ? AppTheme.successColor : AppTheme.warningColor;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Dismissible(
        key: Key(scan.scanId),
        direction: DismissDirection.endToStart,
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 20),
          decoration: BoxDecoration(
            color: AppTheme.errorColor,
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Icon(Icons.delete_outline, color: Colors.white, size: 28),
        ),
        confirmDismiss: (_) => _deleteScan(scan),
        child: InkWell(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => ResultsScreen(result: scan)),
            );
          },
          borderRadius: BorderRadius.circular(20),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.03),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              children: [
                // Icon with gradient back
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        statusColor.withOpacity(0.2),
                        statusColor.withOpacity(0.05),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      scan.predictionEmoji,
                      style: const TextStyle(fontSize: 28),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                
                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            scan.predictionLabel,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          Text(
                            _formatDate(scan.timestamp ?? DateTime.now()),
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textTertiary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: statusColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              '${(scan.confidence * 100).toInt()}% Confidence',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: statusColor,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(Icons.timer_outlined, size: 14, color: AppTheme.textTertiary),
                          const SizedBox(width: 4),
                          Text(
                            '${scan.duration.toStringAsFixed(1)}s',
                            style: TextStyle(fontSize: 12, color: AppTheme.textTertiary),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 4),
                Icon(Icons.chevron_right_rounded, color: AppTheme.textTertiary.withOpacity(0.5)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final scanDate = DateTime(date.year, date.month, date.day);

    String timeStr = '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

    if (scanDate == today) {
      return 'Today, $timeStr';
    } else if (scanDate == yesterday) {
      return 'Yesterday, $timeStr';
    } else if (now.difference(date).inDays < 7) {
      final List<String> days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      return '${days[date.weekday - 1]}, $timeStr';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }
}

