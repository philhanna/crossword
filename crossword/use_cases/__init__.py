"""
Use-case classes for the crossword application.

These classes implement application business logic, coordinating between
domain models and ports (adapters). They are independent of any delivery
mechanism (HTTP, CLI, etc.) and have no framework dependencies.

Use-cases are instantiated with constructor injection:
  grid_uc = GridUseCases(persistence_port)
  puzzle_uc = PuzzleUseCases(persistence_port, word_list_port)
  export_uc = ExportUseCases(export_port)
"""
