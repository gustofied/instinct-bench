#!/bin/sh
set -eu

evidence open record-c
evidence open record-a
evidence open record-d
evidence answer INSUFFICIENT:search-api-2026.07.22.5,cache-router-2026.07.22.2
