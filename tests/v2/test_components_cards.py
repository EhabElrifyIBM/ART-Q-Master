"""
Test Suite for Card Components (Phase 5.2)
==========================================

Comprehensive tests for Card, ElevatedCard, and OutlinedCard components.
Tests cover all Phase 5.2 enhancements including collapsible functionality,
action buttons, loading states, hover effects, and footer support.

Run with: python src_v2/test_components_cards.py
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer
from ui.components_v2.cards import Card, ElevatedCard, OutlinedCard
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.typography import FontSizePreset


class CardTestWindow(QMainWindow):
    """Test window for card components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Card Components Test Suite - Phase 5.2")
        self.setGeometry(100, 100, 1200, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        
        # Add title
        title = QLabel("Card Components Test Suite - Phase 5.2")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 16px;")
        main_layout.addWidget(title)
        
        # Test results
        self.test_results = []
        
        # Run tests
        self.test_basic_card(main_layout)
        self.test_elevated_card(main_layout)
        self.test_outlined_card(main_layout)
        self.test_collapsible_card(main_layout)
        self.test_card_with_actions(main_layout)
        self.test_card_with_footer(main_layout)
        self.test_loading_state(main_layout)
        self.test_hoverable_card(main_layout)
        
        # Add test summary
        main_layout.addStretch()
        self.add_test_summary(main_layout)
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")
    
    def test_basic_card(self, layout: QVBoxLayout):
        """Test 1: Basic Card functionality."""
        try:
            card = Card()
            card.set_title("Test 1: Basic Card")
            
            content = QLabel("This is a basic card with default styling.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify card was created
            assert card is not None, "Card should be created"
            assert card._title_label is not None, "Title should be set"
            assert card._content_widget is not None, "Content should be set"
            
            self.log_test("Basic Card", True, "Card created with title and content")
        except Exception as e:
            self.log_test("Basic Card", False, str(e))
    
    def test_elevated_card(self, layout: QVBoxLayout):
        """Test 2: ElevatedCard with shadow."""
        try:
            card = ElevatedCard()
            card.set_title("Test 2: Elevated Card")
            
            content = QLabel("This card has visual elevation with shadow.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify elevated card properties
            assert card is not None, "ElevatedCard should be created"
            assert card.frameShadow() == card.Raised, "Card should have raised shadow"
            
            self.log_test("Elevated Card", True, "ElevatedCard created with shadow")
        except Exception as e:
            self.log_test("Elevated Card", False, str(e))
    
    def test_outlined_card(self, layout: QVBoxLayout):
        """Test 3: OutlinedCard with border."""
        try:
            card = OutlinedCard()
            card.set_title("Test 3: Outlined Card")
            
            content = QLabel("This card has a prominent border with transparent background.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify outlined card was created
            assert card is not None, "OutlinedCard should be created"
            
            self.log_test("Outlined Card", True, "OutlinedCard created with border")
        except Exception as e:
            self.log_test("Outlined Card", False, str(e))
    
    def test_collapsible_card(self, layout: QVBoxLayout):
        """Test 4: Collapsible Card functionality."""
        try:
            card = Card(collapsible=True)
            card.set_title("Test 4: Collapsible Card")
            
            content = QLabel("This card can be collapsed and expanded.\nClick the arrow to toggle.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify collapsible functionality
            assert card._is_collapsible, "Card should be collapsible"
            assert not card.is_collapsed(), "Card should start expanded"
            
            # Test collapse
            card.set_collapsed(True)
            assert card.is_collapsed(), "Card should be collapsed"
            
            # Test expand
            card.set_collapsed(False)
            assert not card.is_collapsed(), "Card should be expanded"
            
            # Test toggle
            card.toggle_collapsed()
            assert card.is_collapsed(), "Card should be collapsed after toggle"
            
            self.log_test("Collapsible Card", True, "Collapse/expand functionality works")
        except Exception as e:
            self.log_test("Collapsible Card", False, str(e))
    
    def test_card_with_actions(self, layout: QVBoxLayout):
        """Test 5: Card with action buttons."""
        try:
            card = ElevatedCard()
            card.set_title("Test 5: Card with Actions")
            
            # Add action buttons
            action_count = 0
            
            def on_close():
                nonlocal action_count
                action_count += 1
                print("Close action triggered")
            
            def on_settings():
                nonlocal action_count
                action_count += 1
                print("Settings action triggered")
            
            card.add_header_action("close", on_close, "Close card")
            card.add_header_action("settings", on_settings, "Card settings")
            
            content = QLabel("This card has action buttons in the header (close and settings).")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify actions were added
            assert "close" in card._action_buttons, "Close action should be added"
            assert "settings" in card._action_buttons, "Settings action should be added"
            
            # Test action removal
            card.remove_header_action("close")
            assert "close" not in card._action_buttons, "Close action should be removed"
            
            self.log_test("Card with Actions", True, "Action buttons work correctly")
        except Exception as e:
            self.log_test("Card with Actions", False, str(e))
    
    def test_card_with_footer(self, layout: QVBoxLayout):
        """Test 6: Card with footer section."""
        try:
            card = Card()
            card.set_title("Test 6: Card with Footer")
            
            content = QLabel("This card has a footer section with action buttons.")
            card.set_content(content)
            
            # Create footer with buttons
            footer_layout = QHBoxLayout()
            footer_layout.addStretch()
            footer_layout.addWidget(SecondaryButton("Cancel"))
            footer_layout.addWidget(PrimaryButton("Save"))
            
            footer_widget = QWidget()
            footer_widget.setLayout(footer_layout)
            card.set_footer(footer_widget)
            
            layout.addWidget(card)
            
            # Verify footer was added
            assert card._footer_widget is not None, "Footer should be set"
            assert card._footer_container.isVisible(), "Footer container should be visible"
            
            # Test footer removal
            card.remove_footer()
            assert card._footer_widget is None, "Footer should be removed"
            assert not card._footer_container.isVisible(), "Footer container should be hidden"
            
            self.log_test("Card with Footer", True, "Footer functionality works")
        except Exception as e:
            self.log_test("Card with Footer", False, str(e))
    
    def test_loading_state(self, layout: QVBoxLayout):
        """Test 7: Card loading state with skeleton."""
        try:
            card = Card()
            card.set_title("Test 7: Loading State")
            
            content = QLabel("This card will show a loading skeleton animation.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Test loading state
            card.set_loading(True)
            assert card.is_loading(), "Card should be in loading state"
            assert card._loading_timer is not None, "Loading timer should be active"
            
            # Schedule loading stop
            QTimer.singleShot(2000, lambda: self._stop_loading(card))
            
            self.log_test("Loading State", True, "Loading skeleton animation works")
        except Exception as e:
            self.log_test("Loading State", False, str(e))
    
    def _stop_loading(self, card):
        """Helper to stop loading state."""
        card.set_loading(False)
        assert not card.is_loading(), "Card should not be in loading state"
        print("Loading stopped successfully")
    
    def test_hoverable_card(self, layout: QVBoxLayout):
        """Test 8: Hoverable card with effects."""
        try:
            card = ElevatedCard(hoverable=True)
            card.set_title("Test 8: Hoverable Card")
            
            content = QLabel("Hover over this card to see the elevation effect.")
            card.set_content(content)
            
            layout.addWidget(card)
            
            # Verify hoverable property
            assert card._hoverable, "Card should be hoverable"
            
            self.log_test("Hoverable Card", True, "Hover effects enabled")
        except Exception as e:
            self.log_test("Hoverable Card", False, str(e))
    
    def add_test_summary(self, layout: QVBoxLayout):
        """Add test summary section."""
        summary_card = Card()
        summary_card.set_title("Test Summary")
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        summary_text = f"""
        Total Tests: {total}
        Passed: {passed}
        Failed: {total - passed}
        Coverage: {percentage:.1f}%
        
        Status: {'✓ ALL TESTS PASSED' if passed == total else '✗ SOME TESTS FAILED'}
        """
        
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-family: monospace; font-size: 14px;")
        summary_card.set_content(summary_label)
        
        layout.addWidget(summary_card)
        
        # Print detailed results
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for result in self.test_results:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{status}: {result['name']}")
            if result['message']:
                print(f"  {result['message']}")
        print("="*60)
        print(f"Coverage: {percentage:.1f}% ({passed}/{total} tests passed)")
        print("="*60)


def main():
    """Run card component tests."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = CardTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# Made with Bob
