"""
Quick diagnostic to check if cards are being created and rendered.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer

from ui.components_v2.cards import EnhancedToolCard
from utils.tool_registry import get_tool_definitions


def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Card Rendering Test")
    window.resize(800, 600)
    
    central = QWidget()
    window.setCentralWidget(central)
    
    layout = QVBoxLayout(central)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)
    
    # Add title
    title = QLabel("Card Rendering Test - All 5 Tools")
    title.setStyleSheet("font-size: 24px; font-weight: bold;")
    layout.addWidget(title)
    
    # Create cards for all tools
    tools = list(get_tool_definitions())
    print(f"\nCreating {len(tools)} cards...")
    
    for i, tool in enumerate(tools):
        print(f"{i+1}. Creating card for: {tool.display_name}")
        
        card = EnhancedToolCard(
            tool_id=tool.tool_id,
            tool_name=tool.display_name,
            description=tool.description,
            icon=tool.icon
        )
        
        # Explicitly show and add to layout
        card.show()
        layout.addWidget(card)
        
        print(f"   - Card created: {card}")
        print(f"   - Card visible: {card.isVisible()}")
        print(f"   - Card size: {card.size().width()}x{card.size().height()}")
    
    layout.addStretch()
    
    window.show()
    print(f"\nWindow shown. Check if all {len(tools)} cards are visible.")
    print("Window will close in 5 seconds...")
    
    # Close after 5 seconds
    QTimer.singleShot(5000, app.quit)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# Made with Bob
