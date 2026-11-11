# 1. Deposit is held at Paylane, not charged

Status: accepted (2026-05-14)

## Context

We previously charged the deposit and refunded it at return. Refunds took days and customers complained.

## Decision

The deposit is an authorisation hold at Paylane; it was changed from a charge because a hold releases instantly.

## Consequences

A hold expires after five days, so a longer booking needs a renewed hold.
