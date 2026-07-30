/**
 * cobrar-saldo-subform-page.pom.ts — CobrarSaldoSubformPage POM
 *
 * Page Object Model for the inline "Cobrar saldo" subform.
 * Encapsulates locators + actions for the payment + fiscal charge flow.
 *
 * Methods per 04-validators.yaml test_construction_plan step 7:
 *   fillAmount, selectMethod, selectFiscalDocType, selectCurrency,
 *   toggleEmitInvoice, submit, getErrorAlert, getRetryButton,
 *   getSuccessToast, getFiscalWarning
 *
 * Subform is inline within the AppointmentDrawer (not a modal).
 * Form uses RHF + Zod discriminated union per method.
 * Idempotency key generated client-side UUID on first mount.
 *
 * No assertions in POM methods — only actions + locators.
 *
 * downstream-regression-na: brand-local vitalia E2E POM F2-S1
 *
 * @see 04-validators.yaml § poms_required[2]: CobrarSaldoSubformPage
 * @see SC-1 cobrar saldo end-to-end
 * @see SC-2 payment 503 retry flow
 * @see SC-11 currency override
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PaymentMethod = "tarjeta" | "efectivo" | "transferencia";
export type FiscalDocType = "boleta" | "factura" | "ninguno";
export type Currency = "PEN" | "ARS" | "MXN" | "USD";

export interface CobrarSaldoFormData {
  /** Amount to charge (displayed but usually pre-filled) */
  amount?: number;
  /** Payment method */
  method: PaymentMethod;
  /** Fiscal document type */
  fiscalDocType?: FiscalDocType;
  /** Currency override (defaults to tenant locale) */
  currency?: Currency;
  /** Whether to emit invoice */
  emitInvoice?: boolean;
  /** Optional notes */
  notes?: string;
}

// ---------------------------------------------------------------------------
// CobrarSaldoSubformPage POM
// ---------------------------------------------------------------------------

export class CobrarSaldoSubformPage {
  readonly page: Page;

  // ── Subform container ─────────────────────────────────────────────────────

  /** The subform root container (inline, inside drawer Pago accordion) */
  readonly container: Locator;
  /** Amount display (pre-filled from slot balance) */
  readonly amountDisplay: Locator;
  /** Method select */
  readonly methodSelect: Locator;
  /** Fiscal doc type select */
  readonly fiscalDocTypeSelect: Locator;
  /** Currency select */
  readonly currencySelect: Locator;
  /** Emit invoice toggle */
  readonly emitInvoiceToggle: Locator;
  /** Notes textarea */
  readonly notesTextarea: Locator;
  /** Submit button ("Cobrar {currency} {amount}") */
  readonly submitButton: Locator;
  /** Cancel subform button */
  readonly cancelButton: Locator;

  // ── Feedback locators ─────────────────────────────────────────────────────

  /** Error alert (payment failure) */
  readonly errorAlert: Locator;
  /** Retry button (visible after payment failure) */
  readonly retryButton: Locator;
  /** Success toast notification */
  readonly successToast: Locator;
  /** Fiscal emit warning (saga compensation: payment OK + fiscal 503) */
  readonly fiscalWarning: Locator;
  /** Conflict (409) banner */
  readonly conflictBanner: Locator;

  constructor(page: Page) {
    this.page = page;

    this.container = page.locator('[data-testid="cobrar-saldo-subform"]');
    this.amountDisplay = page.locator(
      '[data-testid="cobrar-saldo-amount-display"]',
    );
    this.methodSelect = page.locator('[data-testid="cobrar-saldo-method"]');
    this.fiscalDocTypeSelect = page.locator(
      '[data-testid="cobrar-saldo-fiscal-doc-type"]',
    );
    this.currencySelect = page.locator(
      '[data-testid="cobrar-saldo-currency"]',
    );
    this.emitInvoiceToggle = page.locator(
      '[data-testid="cobrar-saldo-emit-invoice"]',
    );
    this.notesTextarea = page.locator('[data-testid="cobrar-saldo-notes"]');
    this.submitButton = page.locator(
      '[data-testid="cobrar-saldo-submit-btn"]',
    );
    this.cancelButton = page.locator(
      '[data-testid="cobrar-saldo-cancel-btn"]',
    );

    this.errorAlert = page.locator('[data-testid="cobrar-saldo-error-alert"]');
    this.retryButton = page.locator(
      '[data-testid="cobrar-saldo-retry-btn"]',
    );
    this.successToast = page.locator('[data-testid="cobrar-saldo-toast-success"]');
    this.fiscalWarning = page.locator(
      '[data-testid="cobrar-saldo-fiscal-warning"]',
    );
    this.conflictBanner = page.locator(
      '[data-testid="cobrar-saldo-conflict-banner"]',
    );
  }

  // ── Wait ──────────────────────────────────────────────────────────────────

  /**
   * Wait for the subform to be visible and interactive.
   * Called after clicking "Cobrar saldo" button in the drawer.
   */
  async waitForVisible(): Promise<void> {
    await this.container.waitFor({ state: "visible", timeout: 5_000 });
    await this.submitButton.waitFor({ state: "visible", timeout: 3_000 });
  }

  // ── Form fill helpers ─────────────────────────────────────────────────────

  /**
   * Fill the amount field (usually pre-filled; use to override).
   */
  async fillAmount(amount: number): Promise<void> {
    const amountInput = this.page.locator(
      '[data-testid="cobrar-saldo-amount-input"]',
    );
    await amountInput.clear();
    await amountInput.fill(String(amount));
  }

  /**
   * Select payment method from the dropdown.
   */
  async selectMethod(method: PaymentMethod): Promise<void> {
    await this.methodSelect.selectOption(method);
  }

  /**
   * Select fiscal document type.
   */
  async selectFiscalDocType(docType: FiscalDocType): Promise<void> {
    await this.fiscalDocTypeSelect.selectOption(docType);
  }

  /**
   * Select currency override.
   * Tenant default is pre-selected; use to override per transaction.
   */
  async selectCurrency(currency: Currency): Promise<void> {
    await this.currencySelect.selectOption(currency);
  }

  /**
   * Toggle the "Emitir comprobante" switch.
   * @param enabled - true to enable, false to disable
   */
  async toggleEmitInvoice(enabled: boolean): Promise<void> {
    const isChecked = await this.emitInvoiceToggle.isChecked();
    if (isChecked !== enabled) {
      await this.emitInvoiceToggle.click();
    }
  }

  /**
   * Fill the complete subform with provided data.
   */
  async fillForm(data: CobrarSaldoFormData): Promise<void> {
    if (data.amount !== undefined) {
      await this.fillAmount(data.amount);
    }
    await this.selectMethod(data.method);
    if (data.fiscalDocType !== undefined) {
      await this.selectFiscalDocType(data.fiscalDocType);
    }
    if (data.currency !== undefined) {
      await this.selectCurrency(data.currency);
    }
    if (data.emitInvoice !== undefined) {
      await this.toggleEmitInvoice(data.emitInvoice);
    }
    if (data.notes !== undefined) {
      await this.notesTextarea.fill(data.notes);
    }
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  /**
   * Click the submit button ("Cobrar {currency} {amount}").
   * Does NOT wait for response — callers handle assertions.
   */
  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Click retry button (shown after payment failure).
   */
  async clickRetry(): Promise<void> {
    await this.retryButton.click();
  }

  // ── Feedback getters ──────────────────────────────────────────────────────

  /**
   * Get the error alert locator.
   * Visible after payment failure (SC-2 503, SC-5 409).
   */
  getErrorAlert(): Locator {
    return this.errorAlert;
  }

  /**
   * Get the retry button locator.
   */
  getRetryButton(): Locator {
    return this.retryButton;
  }

  /**
   * Wait for the success toast to appear.
   * Toast shows "Cobro {currency} {amount} + boleta emitida" on happy path.
   */
  async waitForSuccessToast(): Promise<void> {
    await this.successToast.waitFor({ state: "visible", timeout: 10_000 });
  }

  /**
   * Get the fiscal warning locator.
   * Visible when payment succeeds but fiscal emit returned 503 (saga compensation).
   */
  getFiscalWarning(): Locator {
    return this.fiscalWarning;
  }

  /**
   * Get the error message text from the error alert.
   */
  async getErrorMessage(): Promise<string> {
    return (await this.errorAlert.textContent()) ?? "";
  }

  /**
   * Get the conflict banner text (409 optimistic lock violation).
   */
  async getConflictMessage(): Promise<string> {
    return (await this.conflictBanner.textContent()) ?? "";
  }

  /**
   * Wait for the subform to disappear (collapsed after successful charge).
   */
  async waitForCollapsed(): Promise<void> {
    await this.container.waitFor({ state: "hidden", timeout: 8_000 });
  }
}
