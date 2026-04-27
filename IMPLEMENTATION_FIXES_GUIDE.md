# Implementation Guide: Payment System Fixes for Production

## Overview
This guide details the **critical fixes** made to ensure platform commission is paid to Gabomazone's account when C2C orders are completed.

**Status**: 2 Critical Issues Fixed ✅

---

## Changes Made

### 1. Platform Commission Payout Integration ✅

**Files Modified**:
- `payments/escrow_service.py` - Added `_pay_platform_commission()` method
- `c2c/models.py` - Added `PLATFORM_PAID` event type
- `project/settings.py` - Added `GABOMAZONE_PLATFORM_MOBILE_NUMBER` setting
- `c2c/migrations/0016_*.py` - Migration for event type

**What Changed**:
```python
# Before: Vendor gets paid, platform commission stuck in escrow
release_escrow_for_c2c_order(c2c_order):
    → Disburses seller_net to vendor ✅
    → Platform commission stays in escrow ❌

# After: Both vendor AND platform get paid
release_escrow_for_c2c_order(c2c_order):
    → Disburses seller_net to vendor ✅
    → CALLS _pay_platform_commission() ✅
    → Disburses platform_commission to Gabomazone ✅
    → Logs both in C2CPaymentEvent for audit ✅
```

---

## Configuration Required (CRITICAL)

You must configure the platform mobile number before deploying:

### Step 1: Add Environment Variable
**File**: `.env` (in gabomazone-app directory)

```bash
# Numéro mobile Gabomazone pour recevoir les commissions
GABOMAZONE_PLATFORM_MOBILE_NUMBER=+24101234567
```

**Format**: 
- International format with country code
- Example: `+241` (Gabon) + phone number
- Must be the same mobile money account configured in SingPay

### Step 2: Verify SingPay Configuration
The following must already be in `.env`:
```bash
SINGPAY_API_KEY=your_api_key
SINGPAY_API_SECRET=your_api_secret
SINGPAY_MERCHANT_ID=your_merchant_id
SINGPAY_DISBURSEMENT_ID=your_disbursement_id
SINGPAY_ENVIRONMENT=production  # For production
```

### Step 3: Run Migrations
```bash
cd gabomazone-app
python manage.py migrate c2c
```

This applies the migration to add the `PLATFORM_PAID` event type to C2CPaymentEvent.

---

## How It Works (Updated Flow)

### Payment Journey (with fixes)

```
1. User initiates C2C payment
   ↓
2. SingPay escrow holds full amount (buyer_total)
   ↓
3. Webhook confirms payment success
   ├─ Sets escrow_status = ESCROW_PENDING
   ├─ Creates C2CPaymentEvent.PAID_ESCROW
   └─ Waits for delivery confirmation
   ↓
4. Buyer + Seller confirm handover and exchange codes
   ↓
5. Codes verified by system
   ↓
6. Order status → COMPLETED
   ↓
7. release_escrow_for_c2c_order() called automatically OR via admin
   ├─ Initiates SingPay disbursement #1: seller_net to vendor
   │   └─ Amount: final_price - commission
   │   └─ Recipient: vendor's mobile money account
   │   └─ Creates C2CPaymentEvent.RELEASED
   │
   ├─ Calls _pay_platform_commission() ← NEW FIX
   │   └─ Initiates SingPay disbursement #2: platform_commission to Gabomazone
   │   └─ Amount: commission amount
   │   └─ Recipient: GABOMAZONE_PLATFORM_MOBILE_NUMBER
   │   └─ Creates C2CPaymentEvent.PLATFORM_PAID
   │
   ├─ Updates transaction.escrow_status = ESCROW_RELEASED
   └─ Returns success with both disbursement IDs
   ↓
8. Both parties receive their respective payments ✅
   ├─ Vendor: seller_net FCFA
   ├─ Gabomazone: platform_commission FCFA
   └─ Buyer: Kept the product, paid buyer_total
```

---

## Testing Checklist (Before Production)

### Test 1: Configuration
- [ ] Verify `.env` contains `GABOMAZONE_PLATFORM_MOBILE_NUMBER`
- [ ] Verify SingPay credentials are correct
- [ ] Verify environment is set to `production` (not sandbox)

### Test 2: End-to-End Flow
- [ ] Create a test C2C order (e.g., 50,000 FCFA)
- [ ] Verify commission calculated correctly:
  - Final price: 50,000 FCFA (6% tier)
  - Commission: 3,000 FCFA
  - Seller_net: 47,000 FCFA
  - Buyer_total: 50,000 FCFA

- [ ] Complete payment successfully
- [ ] Verify in admin:
  - C2COrder status = PAID
  - escrow_status = ESCROW_PENDING
  - C2CPaymentEvent shows PAID_ESCROW entry

### Test 3: Delivery and Release
- [ ] Confirm handover (both buyer + seller)
- [ ] Exchange delivery codes
- [ ] Verify codes (buyer, then seller)
- [ ] Mark order as COMPLETED

- [ ] **Option A (Automatic)**: If auto-release is configured
  - Wait and check if escrow released automatically
  
- [ ] **Option B (Manual)**: Via admin
  - Go to C2C Order admin
  - Select order
  - Choose action: "Libérer l'escrow (manuel)"
  - Click "Appliquer"

### Test 4: Payment Verification
- [ ] Check C2CPaymentEvent log for TWO disbursements:
  - RELEASED (vendor_net to vendor) ✅
  - PLATFORM_PAID (commission to Gabomazone) ✅

- [ ] Verify in SingPay dashboard:
  - Two disbursement transactions created
  - Both marked as "pending" or "success"
  - Correct amounts and recipients

- [ ] Verify mobile money accounts:
  - Vendor receives 47,000 FCFA (or equivalent) ✅
  - Gabomazone receives 3,000 FCFA (or equivalent) ✅

### Test 5: Admin Audit
- [ ] C2COrderAdmin shows all commission details:
  - buyer_commission
  - seller_commission
  - platform_commission
  - seller_net
  - buyer_total

- [ ] C2CPaymentEvent inline shows all event types
- [ ] Transaction SingPay IDs visible in order detail

---

## Monitoring in Production

### Daily Checks
1. **Admin Dashboard**
   - Filter C2COrder by date
   - Check commission amounts
   - Verify all orders show payment events

2. **SingPay Dashboard**
   - Check disbursement status
   - Look for pending or failed transfers
   - Verify amounts match orders

3. **Mobile Money Account**
   - Verify daily deposits for commissions
   - Check reconciliation with admin numbers

### Weekly Report Template
```
C2C Orders Summary (Week of April 21-27):
- Total orders completed: X
- Total commission collected: Y FCFA
- Total vendor payments: Z FCFA
- Platform revenue: Y FCFA
- Failed disbursements: 0
- Pending transfers: X (should resolve within 24h)

Actions taken:
- None
```

### Alert Thresholds
🔴 **Escalate immediately if**:
- Any disbursement fails (check SingPay dashboard)
- Commission collected ≠ Disbursement amounts
- C2CPaymentEvent missing PLATFORM_PAID entries
- Orders stuck with escrow_status = ESCROW_PENDING after 7+ days

---

## Troubleshooting

### Issue: "GABOMAZONE_PLATFORM_MOBILE_NUMBER not configured"
**Solution**:
1. Edit `.env` and add the variable
2. Restart Django application
3. Retry the order release

### Issue: Disbursement to platform fails with "Invalid phone number"
**Solution**:
1. Verify phone format (must include country code)
2. Check SingPay supports this phone number
3. Test with `singpay_service.init_disbursement()` directly in Django shell

### Issue: Vendor payment succeeds but platform payment fails
**Solution**:
1. Check `GABOMAZONE_PLATFORM_MOBILE_NUMBER` is correct
2. Verify SingPay account has sufficient balance
3. Contact SingPay support - escrow was held but disbursement failed
4. Create manual refund via admin action "Annuler et rembourser"

### Issue: Order stuck with escrow_status = ESCROW_PENDING
**Solution**:
1. Check C2COrder.status == COMPLETED
2. Manually trigger escrow release via admin
3. Check logs for `_pay_platform_commission` errors
4. Verify SingPay disbursement_id was created

---

## Code Review Summary

### Modified Files

**1. `payments/escrow_service.py`**
- Added `_pay_platform_commission()` static method
- Calls `singpay_service.init_disbursement()` for platform commission
- Creates C2CPaymentEvent.PLATFORM_PAID for audit trail
- Modified `release_escrow_for_c2c_order()` to call new method

**2. `c2c/models.py`**
- Added `PLATFORM_PAID = 'platform_paid'` constant
- Updated `EVENT_TYPE_CHOICES` with new event type

**3. `project/settings.py`**
- Added `GABOMAZONE_PLATFORM_MOBILE_NUMBER` configuration

**4. `c2c/migrations/0016_*.py` (NEW)**
- Migration file to update EVENT_TYPE_CHOICES in database

### No Changes Made To
- ✅ Commission calculation logic (correct as-is)
- ✅ Escrow mechanism (correct as-is)
- ✅ Vendor disbursement logic (correct as-is)
- ✅ Admin interfaces (display already shows all fields)
- ✅ Payment webhook callback (escrow logic already correct)

---

## Rollback Plan (If Needed)

If there are issues after deployment:

### Quick Rollback
1. **Disable platform commission payout**:
   - Comment out the `_pay_platform_commission()` call in `release_escrow_for_c2c_order()`
   - Restart application
   - Vendor payments continue to work
   - Commission stays in escrow temporarily

2. **Revert to previous commit**:
   ```bash
   git revert HEAD~1
   git push origin main
   ```

### Data Recovery
If platform disbursements fail:
1. Commission funds remain in SingPay escrow (safe)
2. Manual refund available via admin action
3. No data loss - all events logged in C2CPaymentEvent

---

## Production Deployment Checklist

- [ ] `.env` configured with `GABOMAZONE_PLATFORM_MOBILE_NUMBER`
- [ ] All SingPay credentials verified
- [ ] Database migrations applied (`migrate c2c`)
- [ ] Code reviewed and approved
- [ ] Dev/staging tests passed (all 5 test scenarios)
- [ ] Backup database before deployment
- [ ] Monitoring configured (check daily)
- [ ] Support team trained on troubleshooting
- [ ] Documentation updated for operations team

---

## References

### Key Files
- **Escrow Service**: `payments/escrow_service.py:370-445`
- **C2C Models**: `c2c/models.py:585-645` (C2CPaymentEvent)
- **Admin Interface**: `c2c/admin.py:98-387` (C2COrderAdmin)
- **Payment Webhook**: `payments/views.py:637-649` (C2C payment handling)

### SingPay API
- **Disbursement Method**: `/v1/disbursement` (POST)
- **Status Check**: `/v1/transaction/{id}` (GET)
- **Documentation**: https://client.singpay.ga/doc/reference/index.html

### Django ORM
- `SingPayTransaction.objects.create()` - Create transaction record
- `C2CPaymentEvent.log_event()` - Log event for audit trail
- `singpay_service.init_disbursement()` - Initiate SingPay transfer

---

**Last Updated**: 2026-04-24  
**Version**: 1.0  
**Status**: Ready for Production Deployment
