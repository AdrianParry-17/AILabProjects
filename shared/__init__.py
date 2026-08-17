"""Generic, dependency-free utilities shared by every layer of the project.

This package is the lowest layer in the dependency flow (CONVENTION.md § 2).
It imports only the standard library, never `config`, `core`, `data`, `delivery`,
`algorithms`, `visualization` or `ui`.
"""
