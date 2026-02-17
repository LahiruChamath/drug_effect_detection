import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Primary Colors
  static const Color primaryColor = Color(0xFF00C896);      // Fresh teal/mint
  static const Color primaryLight = Color(0xFFE8F8F5);      // Light teal tint
  static const Color primaryDark = Color(0xFF00A67E);       // Darker teal
  
  // Background Colors
  static const Color backgroundColor = Color(0xFFF8FAFB);   // Off-white
  static const Color surfaceColor = Color(0xFFFFFFFF);      // Pure white
  static const Color cardColor = Color(0xFFFFFFFF);         // White cards
  
  // Text Colors
  static const Color textPrimary = Color(0xFF1A1D26);       // Almost black
  static const Color textSecondary = Color(0xFF6B7280);     // Gray
  static const Color textTertiary = Color(0xFF9CA3AF);      // Light gray
  
  // Status Colors
  static const Color successColor = Color(0xFF10B981);      // Green
  static const Color warningColor = Color(0xFFF59E0B);      // Amber
  static const Color errorColor = Color(0xFFEF4444);        // Red
  static const Color infoColor = Color(0xFF3B82F6);         // Blue
  
  // Result Colors
  static const Color normalColor = Color(0xFF10B981);       // Green
  static const Color stimulantColor = Color(0xFFF59E0B);    // Amber
  static const Color depressantColor = Color(0xFF8B5CF6);   // Purple
  static const Color cannabisColor = Color(0xFF22C55E);     // Emerald
  
  // Border & Divider
  static const Color borderColor = Color(0xFFE5E7EB);
  static const Color dividerColor = Color(0xFFF3F4F6);
  
  // Shadows
  static List<BoxShadow> cardShadow = [
    BoxShadow(
      color: Colors.black.withOpacity(0.04),
      blurRadius: 10,
      offset: const Offset(0, 4),
    ),
  ];
  
  static List<BoxShadow> buttonShadow = [
    BoxShadow(
      color: primaryColor.withOpacity(0.3),
      blurRadius: 12,
      offset: const Offset(0, 4),
    ),
  ];

  // Theme Data
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    primaryColor: primaryColor,
    scaffoldBackgroundColor: backgroundColor,
    
    colorScheme: const ColorScheme.light(
      primary: primaryColor,
      secondary: primaryColor,
      surface: surfaceColor,
      error: errorColor,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: textPrimary,
    ),
    
    appBarTheme: AppBarTheme(
      backgroundColor: surfaceColor,
      elevation: 0,
      centerTitle: true,
      systemOverlayStyle: SystemUiOverlayStyle.dark,
      titleTextStyle: GoogleFonts.inter(
        fontSize: 17,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
      iconTheme: const IconThemeData(color: textPrimary),
    ),
    
    textTheme: TextTheme(
      displayLarge: GoogleFonts.inter(
        fontSize: 34,
        fontWeight: FontWeight.bold,
        color: textPrimary,
        letterSpacing: -0.5,
      ),
      displayMedium: GoogleFonts.inter(
        fontSize: 28,
        fontWeight: FontWeight.bold,
        color: textPrimary,
        letterSpacing: -0.5,
      ),
      displaySmall: GoogleFonts.inter(
        fontSize: 22,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
      headlineMedium: GoogleFonts.inter(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
      bodyLarge: GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.normal,
        color: textPrimary,
      ),
      bodyMedium: GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.normal,
        color: textPrimary,
      ),
      bodySmall: GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.normal,
        color: textSecondary,
      ),
      labelLarge: GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: textPrimary,
      ),
    ),
    
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: GoogleFonts.inter(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: textPrimary,
        side: const BorderSide(color: borderColor, width: 1.5),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: GoogleFonts.inter(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: primaryColor,
        textStyle: GoogleFonts.inter(
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: backgroundColor,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: borderColor),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: borderColor),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: primaryColor, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: errorColor, width: 1.5),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
      hintStyle: GoogleFonts.inter(color: textTertiary),
    ),
    
    cardTheme: CardThemeData(
      color: cardColor,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: surfaceColor,
      selectedItemColor: primaryColor,
      unselectedItemColor: textTertiary,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
    
    dividerTheme: const DividerThemeData(
      color: dividerColor,
      thickness: 1,
    ),
  );
}
