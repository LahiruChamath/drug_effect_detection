import 'dart:io';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:csv/csv.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import '../models/scan_result.dart';

class ExportService {
  // Copy to clipboard
  static Future<void> copySummary(ScanResult result) async {
    final text = '''
SafePose Scan Result
Prediction: ${result.predictionLabel} ${result.predictionEmoji}
Confidence: ${(result.confidence * 100).toStringAsFixed(1)}%
Date: ${result.timestamp?.toString() ?? DateTime.now().toString()}

Probabilities:
- Normal: ${((result.probabilities['none'] ?? 0) * 100).toStringAsFixed(1)}%
- Stimulant: ${((result.probabilities['stimulant'] ?? 0) * 100).toStringAsFixed(1)}%
- Depressant: ${((result.probabilities['depressant'] ?? 0) * 100).toStringAsFixed(1)}%
- Cannabis: ${((result.probabilities['cannabis'] ?? 0) * 100).toStringAsFixed(1)}%
''';
    await Clipboard.setData(ClipboardData(text: text));
  }

  // Export CSV
  static Future<void> exportCSV(List<ScanResult> results) async {
    List<List<dynamic>> rows = [];
    // Header
    rows.add([
      'Scan ID',
      'Date',
      'Prediction',
      'Confidence (%)',
      'Normal (%)',
      'Stimulant (%)',
      'Depressant (%)',
      'Cannabis (%)'
    ]);

    for (var r in results) {
      rows.add([
        r.scanId,
        r.timestamp?.toIso8601String() ?? '',
        r.predictionLabel,
        (r.confidence * 100).toStringAsFixed(2),
        ((r.probabilities['none'] ?? 0) * 100).toStringAsFixed(2),
        ((r.probabilities['stimulant'] ?? 0) * 100).toStringAsFixed(2),
        ((r.probabilities['depressant'] ?? 0) * 100).toStringAsFixed(2),
        ((r.probabilities['cannabis'] ?? 0) * 100).toStringAsFixed(2),
      ]);
    }

    String csvContent = Csv().encode(rows);
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/safepose_export.csv');
    await file.writeAsString(csvContent);
    
    await Share.shareXFiles([XFile(file.path)], text: 'SafePose Data Export');
  }

  // Export PDF
  static Future<void> exportPDF(List<ScanResult> results) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        build: (context) => [
          pw.Header(
            level: 0,
            text: 'SafePose Analysis Report',
          ),
          pw.Paragraph(text: 'Generated on: ${DateTime.now().toString()}'),
          pw.SizedBox(height: 20),
          pw.TableHelper.fromTextArray(
            headers: ['Date', 'Prediction', 'Confidence'],
            data: results.map((r) => [
              r.timestamp?.toString().split('.').first ?? '',
              r.predictionLabel,
              '${(r.confidence * 100).toStringAsFixed(1)}%'
            ]).toList(),
          ),
        ],
      ),
    );

    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/safepose_report.pdf');
    await file.writeAsBytes(await pdf.save());

    await Share.shareXFiles([XFile(file.path)], subject: 'SafePose PDF Report');
  }
}
