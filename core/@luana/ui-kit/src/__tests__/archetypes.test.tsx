// canon: design-system-canon.md §6.2 · story-origin: core-ds-foundation
/**
 * archetypes.test.tsx — Validator F-11 for the page archetypes (@luana/ui-kit T-8).
 *
 * Each scaffold composes existing primitives (PageHeader/Toolbar/EntityInfoCard/
 * EmptyState/ErrorState/skeletons/DetailLayout/FormLayout/PageSection). These tests
 * verify the wiring of slots + state precedence, not the primitives themselves.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import {
  ListPageScaffold,
  DetailPageScaffold,
  FormPageScaffold,
  DashboardPageScaffold,
} from "../archetypes";
import { PageHeader, PageSection } from "../layout";

describe("ListPageScaffold (canon @luana/ui-kit)", () => {
  it("renders header + toolbar + children grid", () => {
    render(
      <ListPageScaffold
        header={<PageHeader title="Especialistas" />}
        toolbar={<div data-testid="my-toolbar">filtros</div>}
      >
        <div data-testid="card-1">card</div>
      </ListPageScaffold>,
    );
    expect(screen.getByRole("heading", { name: "Especialistas" })).toBeInTheDocument();
    expect(screen.getByTestId("my-toolbar")).toBeInTheDocument();
    expect(screen.getByTestId("list-page-scaffold-grid")).toBeInTheDocument();
    expect(screen.getByTestId("card-1")).toBeInTheDocument();
  });

  it("shows the empty state when isEmpty (grid not rendered)", () => {
    render(
      <ListPageScaffold header={<PageHeader title="Lista" />} isEmpty>
        <div data-testid="card-1">card</div>
      </ListPageScaffold>,
    );
    expect(screen.getByText("Sin elementos aún")).toBeInTheDocument();
    expect(screen.queryByTestId("list-page-scaffold-grid")).toBeNull();
    expect(screen.queryByTestId("card-1")).toBeNull();
  });

  it("shows the skeleton when isLoading (grid not rendered)", () => {
    render(
      <ListPageScaffold header={<PageHeader title="Lista" />} isLoading>
        <div data-testid="card-1">card</div>
      </ListPageScaffold>,
    );
    expect(screen.getByTestId("list-page-scaffold-skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("list-page-scaffold-grid")).toBeNull();
  });

  it("shows the ErrorState when error is set (takes precedence over loading)", () => {
    render(
      <ListPageScaffold header={<PageHeader title="Lista" />} error isLoading>
        <div data-testid="card-1">card</div>
      </ListPageScaffold>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByTestId("list-page-scaffold-skeleton")).toBeNull();
    expect(screen.queryByTestId("list-page-scaffold-grid")).toBeNull();
  });

  it("renders the pagination slot at the foot", () => {
    render(
      <ListPageScaffold
        header={<PageHeader title="Lista" />}
        pagination={<div data-testid="my-pagination">paginación</div>}
      >
        <div>card</div>
      </ListPageScaffold>,
    );
    expect(screen.getByTestId("my-pagination")).toBeInTheDocument();
  });
});

describe("DetailPageScaffold (canon @luana/ui-kit)", () => {
  it("renders the subnav slot + children content", () => {
    render(
      <DetailPageScaffold subnav={<div data-testid="my-subnav">N3</div>}>
        <div data-testid="leaf-content">contenido del leaf</div>
      </DetailPageScaffold>,
    );
    expect(screen.getByTestId("my-subnav")).toBeInTheDocument();
    expect(screen.getByTestId("leaf-content")).toBeInTheDocument();
  });

  it("renders the header slot when no subnav", () => {
    render(
      <DetailPageScaffold header={<PageHeader title="Detalle" />}>
        <div>contenido</div>
      </DetailPageScaffold>,
    );
    expect(screen.getByRole("heading", { name: "Detalle" })).toBeInTheDocument();
  });

  it("shows the skeleton when isLoading", () => {
    render(
      <DetailPageScaffold subnav={<div>N3</div>} isLoading>
        <div data-testid="leaf-content">contenido</div>
      </DetailPageScaffold>,
    );
    expect(screen.getByTestId("detail-page-scaffold-skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("leaf-content")).toBeNull();
  });

  it("shows the ErrorState when error is set", () => {
    render(
      <DetailPageScaffold subnav={<div>N3</div>} error>
        <div>contenido</div>
      </DetailPageScaffold>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("FormPageScaffold (canon @luana/ui-kit)", () => {
  it("renders header + form children", () => {
    render(
      <FormPageScaffold header={<PageHeader title="Editar perfil" />}>
        <div data-testid="field-group">grupo de campos</div>
      </FormPageScaffold>,
    );
    expect(screen.getByRole("heading", { name: "Editar perfil" })).toBeInTheDocument();
    expect(screen.getByTestId("field-group")).toBeInTheDocument();
  });

  it("renders the autosave indicator slot when provided", () => {
    render(
      <FormPageScaffold
        header={<PageHeader title="Editar" />}
        autosaveIndicator={<div data-testid="my-autosave">guardado</div>}
      >
        <div>grupo</div>
      </FormPageScaffold>,
    );
    expect(screen.getByTestId("my-autosave")).toBeInTheDocument();
  });

  it("does NOT render an autosave slot when not provided", () => {
    render(
      <FormPageScaffold header={<PageHeader title="Editar" />}>
        <div>grupo</div>
      </FormPageScaffold>,
    );
    expect(screen.queryByTestId("my-autosave")).toBeNull();
  });

  it("shows the form skeleton when isLoading (form children not rendered)", () => {
    render(
      <FormPageScaffold header={<PageHeader title="Editar" />} isLoading>
        <div data-testid="field-group">grupo</div>
      </FormPageScaffold>,
    );
    expect(screen.getByTestId("form-page-scaffold-skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("field-group")).toBeNull();
  });
});

describe("DashboardPageScaffold (canon @luana/ui-kit)", () => {
  it("renders header + section children", () => {
    render(
      <DashboardPageScaffold header={<PageHeader title="Resumen" />}>
        <PageSection title="Métricas">
          <div data-testid="metric-block">métricas</div>
        </PageSection>
      </DashboardPageScaffold>,
    );
    expect(screen.getByRole("heading", { name: "Resumen" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Métricas" })).toBeInTheDocument();
    expect(screen.getByTestId("metric-block")).toBeInTheDocument();
  });

  it("shows the skeleton when isLoading (section children not rendered)", () => {
    render(
      <DashboardPageScaffold header={<PageHeader title="Resumen" />} isLoading>
        <PageSection title="Métricas">
          <div data-testid="metric-block">métricas</div>
        </PageSection>
      </DashboardPageScaffold>,
    );
    expect(screen.getByTestId("dashboard-page-scaffold-skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("metric-block")).toBeNull();
  });

  it("shows the ErrorState when error is set", () => {
    render(
      <DashboardPageScaffold header={<PageHeader title="Resumen" />} error>
        <PageSection title="Métricas">
          <div>métricas</div>
        </PageSection>
      </DashboardPageScaffold>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
