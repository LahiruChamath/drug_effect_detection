import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/user.dart';
import 'home_screen.dart';
import 'insights_screen.dart';
import 'history_screen.dart';
import 'profile_screen.dart';

class MainShell extends StatefulWidget {
  final User user;

  const MainShell({super.key, required this.user});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final _homeKey = GlobalKey<HomeScreenState>();
  final _insightsKey = GlobalKey<InsightsScreenState>();
  final _historyKey = GlobalKey<HistoryScreenState>();
  final _profileKey = GlobalKey<ProfileScreenState>();

  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    _screens = [
      HomeScreen(key: _homeKey, user: widget.user),
      InsightsScreen(key: _insightsKey),
      HistoryScreen(key: _historyKey),
      ProfileScreen(key: _profileKey, user: widget.user),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() => _currentIndex = index);
            // Refresh data when switching to a tab
            switch (index) {
              case 0:
                _homeKey.currentState?.refreshData();
                break;
              case 1:
                _insightsKey.currentState?.refreshData();
                break;
              case 2:
                _historyKey.currentState?.refreshData();
                break;
              case 3:
                _profileKey.currentState?.refreshData();
                break;
            }
          },
          type: BottomNavigationBarType.fixed,
          selectedItemColor: AppTheme.primaryColor,
          unselectedItemColor: AppTheme.textSecondary,
          backgroundColor: Colors.white,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined),
              activeIcon: Icon(Icons.home),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.insights_outlined),
              activeIcon: Icon(Icons.insights),
              label: 'Insights',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.history_outlined),
              activeIcon: Icon(Icons.history),
              label: 'History',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }
}
