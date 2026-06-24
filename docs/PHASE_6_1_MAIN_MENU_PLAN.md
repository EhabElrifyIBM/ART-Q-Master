Clear search
    search_bar._input.clear()
    QTest.qWait(100)
    
    assert len(window._tools) == initial_count, "Clear did not restore all tools"
    print("✅ Search functionality works correctly")
    window.close()


def test_recent_tools():
    """Verify recent tools tracking."""
    manager = get_recent_tools_manager()
    manager.clear()
    
    # Add some tools
    manager.add_tool("qcontrol")
    manager.add_tool("assigner")
    manager.add_tool("merger")
    
    recent = manager.get_recent_tools()
    assert len(recent) == 3, f"Expected 3 recent tools, got {len(recent)}"
    assert recent[0] == "merger", "Most recent tool should be first"
    
    print("✅ Recent tools tracking works correctly")


def test_tool_grid_layout():
    """Verify 2-column grid layout."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = V2MainMenu()
    window.show()
    
    # Check grid has 2 columns
    grid = window._tools_grid
    assert grid.columnCount() == 2, f"Expected 2 columns, got {grid.columnCount()}"
    
    print("✅ Tool grid layout correct")
    window.close()


if __name__ == "__main__":
    print("Running Phase 6.1 Main Menu Tests...\n")
    
    test_no_debug_info()
    test_welcome_message()
    test_search_functionality()
    test_recent_tools()
    test_tool_grid_layout()
    
    print("\n✅ All tests passed!")
```

---

## 📊 Implementation Timeline

### Day 1: Components & Infrastructure (6 hours)

**Morning (3 hours):**
- Create SearchBar component (1 hour)
- Create CompactToolCard component (30 min)
- Create EnhancedToolCard component (1 hour)
- Create ProfileButton component (30 min)

**Afternoon (3 hours):**
- Update tool_registry.py with icons and descriptions (30 min)
- Create recent_tools.py tracking system (1 hour)
- Update components_v2/__init__.py exports (15 min)
- Write unit tests for new components (1 hour 15 min)

### Day 2: Integration & Testing (6 hours)

**Morning (3 hours):**
- Update UnifiedToolShell with new layout (2 hours)
- Update V2MainMenu class (30 min)
- Manual testing and bug fixes (30 min)

**Afternoon (3 hours):**
- Create test_main_menu_phase6.py (1 hour)
- Run all tests and fix issues (1 hour)
- Documentation updates (30 min)
- Final review and polish (30 min)

**Total:** 12 hours (2 days at 6 hours/day)

---

## 🔧 Technical Considerations

### Responsive Behavior

**Window Width Breakpoints:**
- < 800px: 1 column grid
- 800-1200px: 2 column grid (default)
- > 1200px: 2 column grid (cards expand)

**Implementation:**
```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    
    # Adjust grid columns based on width
    if self.width() < 800:
        # Switch to 1 column
        self._set_grid_columns(1)
    else:
        # Use 2 columns
        self._set_grid_columns(2)
```

### Performance Optimization

1. **Search Filtering:**
   - Debounce search input (50ms delay)
   - Use case-insensitive string matching
   - Cache filtered results

2. **Recent Tools:**
   - Load once on startup
   - Update file only on tool launch
   - Keep in-memory cache

3. **Component Reuse:**
   - Reuse EnhancedToolCard instances
   - Update content instead of recreating
   - Minimize layout recalculations

### Error Handling

1. **Config Loading:**
   - Fallback to "User" if agent name missing
   - Handle malformed config.json gracefully
   - Log warnings for debugging

2. **Recent Tools:**
   - Handle missing recent_tools.json
   - Validate tool IDs before display
   - Clear invalid entries automatically

3. **Search:**
   - Handle empty search gracefully
   - Show helpful message when no results
   - Maintain UI responsiveness

---

## 📚 Documentation Updates

### Files to Update

1. **UI_REFACTORING_PLAN.md**
   - Mark Phase 6.1 as complete
   - Update status and metrics
   - Add completion date

2. **Component Documentation**
   - Add SearchBar to inputs.md
   - Add CompactToolCard and EnhancedToolCard to cards.md
   - Add ProfileButton to buttons.md

3. **README.md**
   - Update feature list
   - Add screenshots of new main menu
   - Update getting started guide

---

## 🎨 Design Specifications

### Color Usage

**Light Theme:**
- Background: `#f4f4f4` (window_bg)
- Cards: `#ffffff` (surface)
- Text: `#161616` (text_primary)
- Accent: `#0f62fe` (primary)

**Dark Theme:**
- Background: `#161616` (window_bg)
- Cards: `#262626` (surface)
- Text: `#f4f4f4` (text_primary)
- Accent: `#4589ff` (primary)

### Typography Scale

- Welcome Message: `h2` (24px @ normal preset)
- Section Titles: `h3` (20px @ normal preset)
- Tool Names: `h3` (20px @ normal preset)
- Tool Descriptions: `body` (16px @ normal preset)
- Footer: `caption` (12px @ normal preset)

### Spacing

- Page padding: `32px` (Spacing.PAGE_PADDING)
- Section gap: `24px` (Spacing.SECTION_GAP)
- Card gap: `16px` (Spacing.MD)
- Card padding: `16px` (Spacing.CARD_PADDING)

### Icons

**Tool Icons (Emoji):**
- ART Q Control: 🎯
- Assigner: 📊
- Merger: 🔗
- Archiver: 📦
- Reach Rate Calculator: 📈

**UI Icons:**
- Search: 🔍
- Profile: 👤
- Settings: ⚙️
- Help: ❓
- Clear: ✕

---

## 🚀 Deployment Checklist

### Pre-Implementation
- [x] Review current implementation
- [x] Identify all requirements
- [x] Design new layout
- [x] Plan component architecture
- [x] Create implementation plan

### Implementation
- [ ] Create SearchBar component
- [ ] Create CompactToolCard component
- [ ] Create EnhancedToolCard component
- [ ] Create ProfileButton component
- [ ] Update tool_registry.py
- [ ] Create recent_tools.py
- [ ] Update UnifiedToolShell
- [ ] Update V2MainMenu
- [ ] Update component exports

### Testing
- [ ] Unit tests for new components
- [ ] Integration tests for main menu
- [ ] Manual testing checklist
- [ ] Accessibility testing
- [ ] Performance testing
- [ ] Cross-theme testing

### Documentation
- [ ] Update UI_REFACTORING_PLAN.md
- [ ] Update component documentation
- [ ] Add code comments
- [ ] Create user guide
- [ ] Update README.md

### Deployment
- [ ] Code review
- [ ] Merge to main branch
- [ ] Tag release (v2.6.1)
- [ ] Update changelog
- [ ] Notify team

---

## 🎯 Success Metrics

### Quantitative Metrics

1. **Code Quality:**
   - 0 debug information visible
   - 100% of requirements implemented
   - 0 regressions in existing features
   - >80% test coverage

2. **Performance:**
   - Search response < 50ms
   - Tool launch < 200ms
   - Theme switch < 100ms
   - 60 FPS animations

3. **Accessibility:**
   - 100% WCAG 2.1 AA compliance
   - All contrast ratios > 4.5:1
   - All touch targets > 44x44px
   - 100% keyboard navigable

### Qualitative Metrics

1. **User Experience:**
   - Clean, professional appearance
   - Intuitive tool discovery
   - Fast, responsive interactions
   - Consistent with design system

2. **Code Quality:**
   - Well-documented components
   - Reusable, maintainable code
   - Follows established patterns
   - Easy to extend

---

## 🔄 Future Enhancements

### Phase 6.2 Considerations

1. **Tool Categories:**
   - Group tools by area (Operations, Automation, Analytics)
   - Collapsible category sections
   - Category filtering

2. **Tool Statistics:**
   - Show usage count
   - Show last used date
   - Show average execution time

3. **Favorites:**
   - Star favorite tools
   - Favorites section above recent
   - Persist favorites to config

4. **Tool Status Indicators:**
   - Show if tool is currently running
   - Show if tool has updates
   - Show if tool has errors

5. **Quick Actions:**
   - Right-click context menu on tools
   - "Open in new window" option
   - "View documentation" option

---

## 📞 Support & Resources

### Key Files Reference

- Main Menu: [`src_v2/ui/main_menu.py`](../src_v2/ui/main_menu.py)
- Shell: [`src_v2/ui/shell.py`](../src_v2/ui/shell.py)
- Tool Registry: [`src_v2/utils/tool_registry.py`](../src_v2/utils/tool_registry.py)
- Components: [`src_v2/ui/components_v2/`](../src_v2/ui/components_v2/)
- Design System: [`src_v2/ui/design_system.py`](../src_v2/ui/design_system.py)
- Typography: [`src_v2/ui/typography.py`](../src_v2/ui/typography.py)

### Related Documentation

- [UI Refactoring Plan](../src_v2/UI_REFACTORING_PLAN.md)
- [Phase 4 Keyboard Shortcuts](./PHASE_4_KEYBOARD_SHORTCUTS.md)
- [Phase 4 Accessibility](./PHASE_4_ACCESSIBILITY.md)
- [Component Documentation](./components/)

### Contact

For questions or issues during implementation:
- Review this plan document
- Check existing component implementations
- Refer to design system documentation
- Test incrementally as you build

---

## ✅ Final Checklist

Before marking Phase 6.1 as complete:

- [ ] All new components created and tested
- [ ] Main menu updated with new layout
- [ ] All debug information removed
- [ ] Search functionality working
- [ ] Recent tools tracking working
- [ ] Profile button functional
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] User acceptance testing complete

---

**Document Version:** 1.0  
**Created:** April 29, 2026  
**Status:** Ready for Implementation  
**Estimated Completion:** May 1, 2026

---

*This plan provides a comprehensive roadmap for Phase 6.1: Main Menu Modernization. Follow the implementation steps sequentially, test thoroughly at each stage, and refer to the success criteria to ensure all requirements are met.*