"""Generic, dependency-free utilities shared by every layer of the project.

This package is the lowest layer in the dependency flow (ARCHITECTURE.md § 3).
It imports only the standard library, never `config`, `core`, `data`, `delivery`,
`algorithms`, `visualization` or `ui`.
"""
