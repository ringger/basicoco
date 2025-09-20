# TRS-80 Color Computer BASIC Emulator - Forward Development Roadmap

*This roadmap focuses exclusively on future enhancements and development priorities. Current capabilities and recent achievements are documented in README.md and git commit history.*

## Current Architecture Foundation 🏗️

The emulator now has a **clean, well-established architecture** that provides the foundation for future development:

- **✅ Unified Error Handling**: 145+ educational error messages across all modules
- **✅ Clean Method Naming**: `process_*` for internal system vs `execute_*` for user commands
- **✅ Command Registry**: Unified plugin-based command dispatch system
- **✅ Function Registry**: Single source of truth for all BASIC functions
- **✅ Modular Design**: Clear separation of concerns across specialized modules
- **✅ AST-Based Control Structures**: Complete single-line control structure normalization with unified execution model
- **✅ Pytest Framework**: Modern test infrastructure with fixtures and comprehensive coverage
- **✅ Robust GOTO Support**: Non-brittle AST parsing handles both simple and complex control structures

**Architecture Patterns to Maintain:**
- Command registration via `register_commands()` in each module
- Enhanced error context with educational suggestions
- Clear internal/external API boundaries
- Function ownership by `functions.py` module only
- AST-based control structure processing for complex single-line statements
- Pytest fixtures for consistent test setup and execution
- Non-brittle AST parsing that handles control structures with or without colons consistently

## Forward Development Priorities 🎯

### Phase 1: State Management Architecture Enhancement 🏗️

**Create specialized state managers for improved maintainability and clear separation of concerns:**

- **Implement Specialized State Managers**
  - `VariableStateManager` - variables, arrays, and type management
  - `ExecutionStateManager` - program counter, call stacks, loops, execution flow  
  - `IOStateManager` - keyboard buffer, input state, cursor management
  - `GraphicsStateManager` - graphics mode, screen state, cursor positioning
  
- **Refactor State Management Interface**
  - Refactor `clear_interpreter_state()` to delegate to appropriate managers
  - Define clear state clearing policies for NEW, LOAD, RUN operations
  - Establish state isolation boundaries between different concerns
  - Create state snapshots for debugging and program state inspection

- **Architecture Documentation & Testing**
  - Create architecture decision records (ADRs) for all design choices
  - Add integration tests specifically for architectural boundaries
  - Document clear component responsibilities and interfaces
  - Add static analysis rules to enforce architectural decisions

### Phase 2: Essential Disk BASIC File Operations
- **Core File I/O Commands**
  - OPEN "mode",#device,"filename" - Open files for sequential/random access (#1-#15)
  - CLOSE #device - Close opened file buffers
  - PRINT #device, data - Write data to opened file
  - INPUT #device, variables - Read data from opened file
- **Random File Access**
  - FIELD #device, width AS variable$ - Organize file buffer into named fields
  - GET #device [,record] - Read specific record from random access file
  - PUT #device [,record] - Write current buffer to random access file

### Phase 3: Advanced System Functions & Memory Simulation
- **Authentic Memory Access**
  - PEEK(address) - Read simulated memory location with TRS-80 memory map
  - POKE address, value - Write to simulated memory location
  - VARPTR(variable) - Return memory address of variable
  - Memory visualization tools for educational use
- **System Functions**
  - MEM - Return available memory
  - TIMER - System timer value for precise timing operations
  - FRE(0) - Free memory function
  - RANDOMIZE [seed] - Initialize random seed with better distribution
- **Machine Language Support**
  - EXEC [address] - Execute machine language program
  - USR[n](parameter) - Call user-defined machine language subroutine
  - LOADM "filename" [,offset] - Load machine language program from disk
  - SAVEM "filename",start,end,execute - Save machine language program to disk

### Phase 4: Enhanced Disk BASIC Commands
- **Program Management**
  - MERGE "filename" - Merge BASIC program with current program
  - RENAME "oldname","newname" - Rename disk files
  - COPY "source","destination" - Copy files on disk
- **Machine Language Tape Operations**
  - CLOADM "filename" [,offset] - Load machine language from tape
  - CSAVEM "filename",start,end,execute - Save machine language to tape
  - MOTOR ON/OFF - Control cassette motor (no-op)

### Phase 5: Advanced Error Handling & Recovery
- **Structured Error Handling**
  - ON ERROR GOTO line - Error trapping with proper stack management
  - RESUME [line] - Resume execution after error handling
  - ERR - Error code function returning specific error numbers
  - ERL - Error line function showing where error occurred
- **Enhanced Debugging Integration**
  - Integration with CLI client debugging tools
  - Error context preservation and reporting
  - Stack trace visualization for educational debugging

## User Experience Enhancements 🎨

### Next-Generation CLI Experience  
- **Enhanced Terminal Features**
  - Optional retro font rendering for authentic feel
  - Screen scroll behavior matching original hardware behavior
- **Advanced Input Features**
  - Enhanced syntax highlighting during program entry
  - Intelligent line number management and auto-insertion
  - Multi-line editing with proper BASIC formatting
  - Context-aware help system for commands and functions


### Mobile and Accessibility
- **Responsive Design**
  - Touch-friendly interface for tablets
  - Virtual keyboard for mobile devices
  - Gesture controls for common operations
- **Accessibility Features**
  - Screen reader compatibility
  - High contrast mode
  - Keyboard navigation
  - Font size adjustment

## Advanced Graphics Enhancements 🎮

### GET/PUT Operations
- **Advanced Blending Modes**
  - OR, AND, XOR operations for sprite composition
  - PRESET mode (transparent background)
  - PSET mode (opaque background)
  - NOT mode (inverted pixels)
- **Sprite Management**
  - Sprite collision detection
  - Animated sprite sequences
  - Sprite rotation and scaling (non-authentic but useful)

### Enhanced DRAW Command
- **Extended Commands**
  - Relative arc drawing (TA command)
  - Filled shapes (paint-after-draw mode)
  - Pattern fills within drawn shapes
- **Performance Optimization**
  - Batch drawing operations
  - Canvas optimization for complex drawings
  - Background rendering for smooth animation

### Graphics Mode Extensions
- **Additional PMODE Variants**
  - PMODE 5: Higher resolution mode (non-authentic)
  - Custom color palettes
  - Gradient fills and effects
- **Modern Graphics Features**
  - Anti-aliased drawing (optional)
  - PNG/JPEG image loading
  - Graphics export functionality

## Performance and Optimization 🚀

### Execution Speed Enhancement
- **Parser Optimization**
  - Pre-compile programs to optimize repeated execution
  - Expression caching for complex calculations
  - Tokenized program storage for faster parsing
- **Graphics Performance**
  - Canvas layer separation for graphics and text
  - Dirty rectangle updates for partial redraws
  - WebGL acceleration for complex graphics operations

### Memory Management
- **Variable Storage Optimization**
  - Efficient array storage for large datasets
  - String interning for repeated values
  - Garbage collection for unused variables
- **Program Storage**
  - Compressed program storage
  - Incremental loading for large programs
  - Background compilation

## Modern Web Integration 🌐

### Cloud Features
- **Program Sharing**
  - Share programs via shareable URLs
  - Community program library
  - Version control for programs
  - Collaborative editing features
- **Export/Import**
  - Export to authentic .BAS files
  - Import from various BASIC dialects
  - Convert to/from modern programming languages

### Educational Integration
- **Learning Tools**
  - Interactive BASIC tutorials
  - Step-by-step program execution
  - Variable watch windows
  - Memory visualization
- **Curriculum Integration**
  - Pre-built lesson plans
  - Progressive difficulty levels
  - Achievement system for learning milestones

## Technical Architecture Evolution 🏗️

### Parser Enhancement Strategy
- **Tokenization System**
  - Implement full tokenization for complex language features
  - Enable advanced features like multi-line IF/THEN/ELSE
- **AST Generation**
  - Abstract syntax tree for complex expressions
  - Enable advanced optimizations
  - Better error reporting with context

### Extension Architecture
- **Plugin System**
  - Modular command extensions
  - Custom function libraries
  - Third-party graphics engines
- **API Design**
  - RESTful API for program management
  - WebSocket API for real-time collaboration
  - JavaScript API for web integration

## Development Methodology 📋

### Incremental Enhancement
- **Feature Prioritization**
  - User-requested features first
  - Educational value assessment
  - Authentic behavior preservation
- **Testing Strategy**
  - Comprehensive test coverage for all new features
  - Regression testing for existing functionality
  - Performance benchmarking
- **Release Management**
  - Feature flagging for experimental capabilities
  - Semantic versioning
  - Migration guides for breaking changes

### Code Quality Standards
- **Documentation**
  - Inline code documentation
  - API documentation
  - User guides and tutorials
- **Performance Standards**
  - Sub-100ms response time for commands
  - Smooth animation at 60fps for graphics
  - Memory usage optimization

## Architecture Guidelines 🏗️

### Internal Architecture Patterns

#### Method Naming Convention
**CRITICAL**: Maintain clear separation between internal system methods and user command methods:

- **`process_*` methods**: Internal system processing (process_command, process_line, process_statement)
- **`execute_*` methods**: User BASIC commands (execute_if, execute_goto, execute_print)
- **Backwards Compatibility**: External API maintains `process_command()` as alias to `process_command()`

#### Command Registry Architecture
**ESTABLISHED PATTERN**: All BASIC commands use the unified `CommandRegistry` system:

**Adding New Commands:**
1. ✅ **DO**: Add to appropriate module's `register_commands()` method
2. ✅ **DO**: Use the established registration pattern with metadata
3. ❌ **DON'T**: Add hardcoded if/elif chains in `process_statement()`
4. ❌ **DON'T**: Bypass the command registry system

**Registration Pattern:**
```python
def register_commands(self, registry):
    registry.register('COMMAND_NAME', self.execute_method, 
                     category='appropriate_category',
                     description="Command description",
                     syntax="COMMAND syntax",
                     examples=["COMMAND example"])
```

**Function Registry Architecture:**
- All BASIC functions (CHR$, ASC, LEFT$, etc.) are handled by `/emulator/functions.py`
- Functions are registered at module bottom and called during expression evaluation
- ❌ **NEVER** duplicate function implementations in other modules

### Error Handling Standards
**ESTABLISHED PATTERN**: All modules use the Enhanced Error Context system for educational error messages.

**Standard Error Pattern:**
```python
error = self.emulator.error_context.syntax_error(
    "Clear description of what went wrong",
    self.emulator.current_line,
    suggestions=[
        'Specific suggestion for fixing the error',
        'Example of correct syntax',
        'Additional helpful guidance'
    ]
)
return [{'type': 'error', 'message': error.format_detailed()}]
```

**Error Types Available:**
- `syntax_error()` - For invalid BASIC syntax
- `runtime_error()` - For execution-time errors
- `type_error()` - For data type mismatches
- `arithmetic_error()` - For mathematical domain/range errors

**Error Handling Requirements:**
1. ✅ **REQUIRED**: Use enhanced error context with 2-3 helpful suggestions
2. ✅ **REQUIRED**: Provide specific examples of correct syntax
3. ✅ **REQUIRED**: Return `[{'type': 'error', 'message': formatted_message}]` format
4. ❌ **FORBIDDEN**: Generic error messages without educational value

### State Management Boundaries
**Clear Separation of Concerns:**
- `keyboard_buffer` belongs to execution state, NOT cleared during program RUN
- Each state manager has clear ownership boundaries
- `clear_interpreter_state()` only clears program execution state, not input state

## Implementation Notes 🔧

### Browser Compatibility
- **Core Support**
  - Modern browsers with ES6+ support
  - WebSocket and Canvas API requirements
  - Web Audio API for sound features
- **Fallback Strategies**
  - Graceful degradation for missing features
  - Alternative input methods for touch devices
  - Offline functionality with service workers

### Deployment Considerations
- **Scalability**
  - Static file hosting for client-side execution
  - CDN distribution for global access
  - Session storage optimization
- **Security**
  - Content Security Policy implementation
  - XSS protection for user programs
  - Safe evaluation of user expressions

## Additional Missing Commands Inventory 📋

### **Missing String & Conversion Functions**
- **HEX$(number)** - Convert number to hexadecimal string
- **OCT$(number)** - Convert number to octal string  

### **Advanced Graphics Commands**
- **PCLEAR [pages]** - Allocate graphics memory pages
- **PPOINT(x,y)** - Return color of pixel at coordinates
- **Enhanced SCREEN** command with full type/colorset support

### **File Status Functions** 
- **EOF(device)** - Test for end-of-file condition
- **LOC(device)** - Return current file position
- **LOF(device)** - Return file length
- **FREE(drive)** - Return free disk space in granules

### **Advanced Disk Management**
- **BACKUP source_drive TO dest_drive** - Duplicate entire disk contents  
- **DSKINI drive [,name] [,tracks]** - Format/initialize disk
- **VERIFY ON/OFF** - Toggle disk write verification

### **Development & Debug Tools**
- **EDIT line_number** - Edit specific line interactively
- **LLIST** - List program to printer
- **TRON/TROFF** - Trace program execution on/off

*Note: This inventory represents the complete set of authentic TRS-80 Color Computer BASIC and Extended Disk BASIC commands not currently implemented in the emulator.*

## Long-term Vision 🔮

### Advanced Error Features (Future Priority)
- **Enhanced Error Recovery**
  - Smart suggestions analyzing common typos and suggesting corrections
  - Context-aware help with different suggestions based on error location
  - Multi-line error context showing surrounding code lines for complex errors
- **Advanced Source Location**
  - Column tracking for precise error position within lines
  - Error highlighting with visual indicators pointing to exact problem location
  - Code snippets showing problematic code section in error messages
- **Error Analytics**
  - Error pattern recognition to suggest common fixes
  - Learning system that improves suggestions based on usage patterns

### Quality Assurance Framework (Future Priority)
- **Error Message Testing & Polish**
  - Dedicated test suite for error message quality and consistency
  - User experience testing to verify error messages actually help users
  - A/B testing framework for error message effectiveness
- **Documentation & Standards**
  - Comprehensive error message style guide for BASIC programmers
  - Error message localization framework for international users
  - Error message API documentation for extension developers
- **Performance & Monitoring**
  - Error message generation performance optimization
  - Error frequency monitoring and reporting dashboard
  - User feedback collection system for error message improvements

## Important Development Notes

- Always activate the virtual environment before running Python: `source venv/bin/activate`
- When running tests, let them run to completion instead of timing out
- Backend server can be started with comprehensive logging using `./start_server_with_logging.sh` for better debugging
- Use `./monitor_server_logs.sh` in a separate terminal to monitor server output in real-time

## Debugging and Issue Tracking Guidelines

### Architecture Issue Priority
**CRITICAL**: When encountering architectural inconsistencies, these must be treated as **immediate blockers** that prevent feature development until resolved. Examples:
- Duplicate function implementations across modules
- Missing method dependencies or dead code references
- Bypassing established command registry patterns
- Inconsistent error handling patterns
- State management boundary violations
- Method naming convention violations (`process_*` vs `execute_*`)

### Side Issue Management
When encountering **side issues** during debugging or development (bugs, inconsistencies, or missing features discovered while working on the main task):

1. **Do NOT** just mention and forget the issue
2. **DO** add it immediately to the TodoWrite task list at the bottom with status "pending"
3. **Prioritize architectural issues above feature issues**
4. **Example Format**: 
   - "Fix PAUSE command syntax error discovered during testing"
   - "Investigate tuple/int comparison bug in INPUT processing"  
   - "Address missing error messages in command X"
   - "Remove duplicate PRINT implementation found in core.py" (architectural)

This ensures side issues are captured for later resolution and don't get lost in the development process.

### TodoWrite Best Practices
- Mark current work as "in_progress" 
- Complete tasks immediately when finished
- Add newly discovered issues as "pending" tasks
- Keep the todo list current and relevant to ongoing work