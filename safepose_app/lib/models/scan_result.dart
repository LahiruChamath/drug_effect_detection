class ScanResult {
  final String scanId;
  final String prediction;
  final double confidence;
  final Map<String, double> probabilities;
  final List<String> indicators;
  final double detectionRate;
  final int framesAnalyzed;
  final double duration;
  final DateTime? timestamp;

  ScanResult({
    required this.scanId,
    required this.prediction,
    required this.confidence,
    required this.probabilities,
    required this.indicators,
    required this.detectionRate,
    required this.framesAnalyzed,
    required this.duration,
    this.timestamp,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      scanId: json['scan_id'] ?? '',
      prediction: json['prediction'] ?? 'unknown',
      confidence: (json['confidence'] ?? 0).toDouble(),
      probabilities: Map<String, double>.from(
        (json['probabilities'] ?? {}).map(
          (key, value) => MapEntry(key, (value as num).toDouble()),
        ),
      ),
      indicators: List<String>.from(json['indicators'] ?? []),
      detectionRate: (json['detection_rate'] ?? 0).toDouble(),
      framesAnalyzed: json['frames_analyzed'] ?? 0,
      duration: (json['duration'] ?? 0).toDouble(),
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp']) 
          : DateTime.now(),
    );
  }

  String get predictionEmoji {
    switch (prediction.toLowerCase()) {
      case 'none':
        return '🟢';
      case 'stimulant':
        return '⚡';
      case 'depressant':
        return '😴';
      case 'cannabis':
        return '🌿';
      default:
        return '❓';
    }
  }

  String get predictionLabel {
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
        return 'Unknown';
    }
  }

  bool get isNormal => prediction.toLowerCase() == 'none';
}
