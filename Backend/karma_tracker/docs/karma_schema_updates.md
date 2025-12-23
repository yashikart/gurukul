# Karma Chain - Karma Schema Updates

This document summarizes the updates made to the Karma Chain project to implement the additional karma types as specified.

## Changes Made

### 1. Updated token_schema.json

Added the following new karma types to the schema:
- **DridhaKarma** / **AdridhaKarma** (weighted behavioral changeability)
- **SanchitaKarma** (accumulated past karma)
- **PrarabdhaKarma** (current life karma being experienced)
- **Rnanubandhan** (karmic debts & past obligations)

Updated the schema to include numeric weights for Dridha/Adridha/Rnanubandhan that can influence future calculations.

### 2. Created utils/karma_schema.py

Implemented new utility functions for updating each karma type:
- `apply_dridha_adridha_karma()` - Apply DridhaKarma or AdridhaKarma to a user's balance
- `apply_sanchita_karma()` - Apply SanchitaKarma to a user's balance
- `apply_prarabdha_karma()` - Apply PrarabdhaKarma to a user's balance
- `apply_rnanubandhan()` - Apply Rnanubandhan to a user's balance based on severity
- `get_karma_weights()` - Get the weights for different karma types
- `calculate_weighted_karma_score()` - Calculate the total weighted karma score for a user

### 3. Updated config.py

Added new token attributes for the additional karma types with their respective weights, expiry days, and decay rates.

### 4. Updated utils/paap.py

Added `apply_rnanubandhan_tokens()` function to handle Rnanubandhan karma type.

### 5. Created data/karma_actions_dataset.json

Prepared a placeholder dataset of actions with karma references for testing, including:
- Actions that generate positive karma (DharmaPoints, SevaPoints, PunyaTokens)
- Actions that generate negative karma (PaapTokens)
- Actions that affect the new karma types (DridhaKarma, AdridhaKarma, SanchitaKarma, PrarabdhaKarma, Rnanubandhan)

### 6. Created tests/test_karma_schema.py

Implemented comprehensive tests to verify the functionality of all new karma types and utility functions.

## Key Features

1. **Weighted Karma Calculation**: The new karma types include weights that can influence future calculations.
2. **Severity Classes**: Rnanubandhan includes severity classes (minor, medium, major) with different multipliers.
3. **Proper Expiry and Decay**: Each karma type has appropriate expiry days and decay rates.
4. **Backward Compatibility**: All existing functionality remains intact.