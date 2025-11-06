--
-- PostgreSQL database dump
--

\restrict TUkuMkm7IsTf4pQkWCitJxjBgZbYdJyCMsRIqS9MnHIzOT5Je1NsJv5V6g46BBK

-- Dumped from database version 17.6 (Debian 17.6-2.pgdg12+1)
-- Dumped by pg_dump version 17.6 (Ubuntu 17.6-2.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: eesaas_prod_db_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO eesaas_prod_db_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO eesaas_prod_db_user;

--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.app_settings (
    id integer NOT NULL,
    settings jsonb DEFAULT '{}'::jsonb NOT NULL,
    settings_version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    org_id integer
);


ALTER TABLE public.app_settings OWNER TO eesaas_prod_db_user;

--
-- Name: app_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.app_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.app_settings_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: app_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.app_settings_id_seq OWNED BY public.app_settings.id;


--
-- Name: assemblies; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.assemblies (
    id integer NOT NULL,
    name text NOT NULL,
    notes text,
    assembly_code text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    category text,
    subcategory text,
    is_featured boolean DEFAULT false NOT NULL,
    org_id integer
);


ALTER TABLE public.assemblies OWNER TO eesaas_prod_db_user;

--
-- Name: assemblies_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.assemblies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assemblies_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: assemblies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.assemblies_id_seq OWNED BY public.assemblies.id;


--
-- Name: assembly_components; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.assembly_components (
    id integer NOT NULL,
    assembly_id integer NOT NULL,
    material_id integer NOT NULL,
    qty_per_assembly numeric(12,4) NOT NULL,
    sort_order integer,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.assembly_components OWNER TO eesaas_prod_db_user;

--
-- Name: assembly_components_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.assembly_components_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assembly_components_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: assembly_components_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.assembly_components_id_seq OWNED BY public.assembly_components.id;


--
-- Name: billing_customers; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.billing_customers (
    id integer NOT NULL,
    org_id integer NOT NULL,
    stripe_customer_id character varying(64) NOT NULL,
    billing_email character varying(255),
    default_payment_method character varying(64),
    billing_address_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    tax_ids_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.billing_customers OWNER TO eesaas_prod_db_user;

--
-- Name: billing_customers_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.billing_customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.billing_customers_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: billing_customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.billing_customers_id_seq OWNED BY public.billing_customers.id;


--
-- Name: billing_event_logs; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.billing_event_logs (
    id integer NOT NULL,
    stripe_event_id character varying(255) NOT NULL,
    type character varying(80) NOT NULL,
    signature_valid boolean DEFAULT true NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    retries integer DEFAULT 0 NOT NULL,
    notes character varying(255),
    processed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.billing_event_logs OWNER TO eesaas_prod_db_user;

--
-- Name: billing_event_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.billing_event_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.billing_event_logs_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: billing_event_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.billing_event_logs_id_seq OWNED BY public.billing_event_logs.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    email character varying,
    phone character varying,
    city character varying,
    notes text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    company_name character varying,
    contact_name character varying,
    address1 character varying,
    address2 character varying,
    state character varying(2),
    zip character varying(10),
    user_id integer,
    org_id integer
);


ALTER TABLE public.customers OWNER TO eesaas_prod_db_user;

--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customers_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: dje_items; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.dje_items (
    id integer NOT NULL,
    category character varying NOT NULL,
    subcategory character varying,
    description character varying NOT NULL,
    default_unit_cost numeric(12,4) DEFAULT 0 NOT NULL,
    cost_code text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    vendor character varying,
    org_id integer,
    is_seed boolean DEFAULT false NOT NULL,
    seed_pack character varying,
    seed_version integer,
    seed_key character varying,
    seeded_at timestamp with time zone
);


ALTER TABLE public.dje_items OWNER TO eesaas_prod_db_user;

--
-- Name: dje_items_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.dje_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dje_items_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: dje_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.dje_items_id_seq OWNED BY public.dje_items.id;


--
-- Name: email_logs; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.email_logs (
    id integer NOT NULL,
    user_id integer,
    to_email character varying(320) NOT NULL,
    template character varying(64) NOT NULL,
    subject character varying(200) NOT NULL,
    provider_msg_id character varying(128),
    status character varying(20) DEFAULT 'sent'::character varying NOT NULL,
    meta json DEFAULT '{}'::json NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.email_logs OWNER TO eesaas_prod_db_user;

--
-- Name: email_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.email_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_logs_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: email_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.email_logs_id_seq OWNED BY public.email_logs.id;


--
-- Name: estimates; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.estimates (
    id integer NOT NULL,
    customer_id integer,
    name character varying(255) NOT NULL,
    project_address character varying(255),
    project_ref character varying(255),
    status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    settings_snapshot jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    work_payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    user_id integer,
    org_id integer
);


ALTER TABLE public.estimates OWNER TO eesaas_prod_db_user;

--
-- Name: estimates_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.estimates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.estimates_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: estimates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.estimates_id_seq OWNED BY public.estimates.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    org_id integer,
    user_id integer,
    path character varying(255),
    message text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.feedback OWNER TO eesaas_prod_db_user;

--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feedback_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: materials; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.materials (
    id integer NOT NULL,
    material_type character varying,
    sku character varying,
    manufacturer character varying,
    item_description character varying,
    vendor character varying,
    price numeric(10,4),
    labor_unit numeric(10,4),
    unit_quantity_size integer NOT NULL,
    material_cost_code text,
    mat_cost_code_desc text,
    labor_cost_code text,
    labor_cost_code_desc text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    org_id integer,
    is_seed boolean DEFAULT false NOT NULL,
    seed_pack character varying,
    seed_version integer,
    seed_key character varying,
    seeded_at timestamp with time zone
);


ALTER TABLE public.materials OWNER TO eesaas_prod_db_user;

--
-- Name: materials_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.materials_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: materials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.materials_id_seq OWNED BY public.materials.id;


--
-- Name: org_memberships; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.org_memberships (
    id integer NOT NULL,
    org_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(20) DEFAULT 'member'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_org_memberships_role_valid CHECK (((role)::text = ANY ((ARRAY['owner'::character varying, 'admin'::character varying, 'member'::character varying])::text[])))
);


ALTER TABLE public.org_memberships OWNER TO eesaas_prod_db_user;

--
-- Name: org_memberships_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.org_memberships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.org_memberships_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: org_memberships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.org_memberships_id_seq OWNED BY public.org_memberships.id;


--
-- Name: orgs; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.orgs (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.orgs OWNER TO eesaas_prod_db_user;

--
-- Name: orgs_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.orgs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orgs_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: orgs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.orgs_id_seq OWNED BY public.orgs.id;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.subscriptions (
    id integer NOT NULL,
    org_id integer NOT NULL,
    stripe_subscription_id character varying(64) NOT NULL,
    product_id character varying(64) NOT NULL,
    price_id character varying(64) NOT NULL,
    status character varying(32) DEFAULT 'incomplete'::character varying NOT NULL,
    cancel_at timestamp with time zone,
    cancel_at_period_end boolean DEFAULT false NOT NULL,
    current_period_end timestamp with time zone,
    quantity integer DEFAULT 1 NOT NULL,
    entitlements_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.subscriptions OWNER TO eesaas_prod_db_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptions_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    org_id integer,
    email_verified_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO eesaas_prod_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: eesaas_prod_db_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO eesaas_prod_db_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: eesaas_prod_db_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: app_settings id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.app_settings ALTER COLUMN id SET DEFAULT nextval('public.app_settings_id_seq'::regclass);


--
-- Name: assemblies id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assemblies ALTER COLUMN id SET DEFAULT nextval('public.assemblies_id_seq'::regclass);


--
-- Name: assembly_components id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assembly_components ALTER COLUMN id SET DEFAULT nextval('public.assembly_components_id_seq'::regclass);


--
-- Name: billing_customers id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_customers ALTER COLUMN id SET DEFAULT nextval('public.billing_customers_id_seq'::regclass);


--
-- Name: billing_event_logs id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_event_logs ALTER COLUMN id SET DEFAULT nextval('public.billing_event_logs_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: dje_items id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.dje_items ALTER COLUMN id SET DEFAULT nextval('public.dje_items_id_seq'::regclass);


--
-- Name: email_logs id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.email_logs ALTER COLUMN id SET DEFAULT nextval('public.email_logs_id_seq'::regclass);


--
-- Name: estimates id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.estimates ALTER COLUMN id SET DEFAULT nextval('public.estimates_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: materials id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.materials ALTER COLUMN id SET DEFAULT nextval('public.materials_id_seq'::regclass);


--
-- Name: org_memberships id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.org_memberships ALTER COLUMN id SET DEFAULT nextval('public.org_memberships_id_seq'::regclass);


--
-- Name: orgs id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.orgs ALTER COLUMN id SET DEFAULT nextval('public.orgs_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: app_settings app_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT app_settings_pkey PRIMARY KEY (id);


--
-- Name: assemblies assemblies_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assemblies
    ADD CONSTRAINT assemblies_pkey PRIMARY KEY (id);


--
-- Name: assembly_components assembly_components_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assembly_components
    ADD CONSTRAINT assembly_components_pkey PRIMARY KEY (id);


--
-- Name: billing_customers billing_customers_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_customers
    ADD CONSTRAINT billing_customers_pkey PRIMARY KEY (id);


--
-- Name: billing_customers billing_customers_stripe_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_customers
    ADD CONSTRAINT billing_customers_stripe_customer_id_key UNIQUE (stripe_customer_id);


--
-- Name: billing_event_logs billing_event_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_event_logs
    ADD CONSTRAINT billing_event_logs_pkey PRIMARY KEY (id);


--
-- Name: billing_event_logs billing_event_logs_stripe_event_id_key; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_event_logs
    ADD CONSTRAINT billing_event_logs_stripe_event_id_key UNIQUE (stripe_event_id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: dje_items dje_items_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.dje_items
    ADD CONSTRAINT dje_items_pkey PRIMARY KEY (id);


--
-- Name: email_logs email_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_pkey PRIMARY KEY (id);


--
-- Name: estimates estimates_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT estimates_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: materials materials_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (id);


--
-- Name: org_memberships org_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT org_memberships_pkey PRIMARY KEY (id);


--
-- Name: orgs orgs_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.orgs
    ADD CONSTRAINT orgs_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_stripe_subscription_id_key; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_stripe_subscription_id_key UNIQUE (stripe_subscription_id);


--
-- Name: org_memberships uq_org_memberships_org_user; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT uq_org_memberships_org_user UNIQUE (org_id, user_id);


--
-- Name: subscriptions uq_subscriptions_org_id; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT uq_subscriptions_org_id UNIQUE (org_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_ac_assembly; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_ac_assembly ON public.assembly_components USING btree (assembly_id);


--
-- Name: ix_ac_assembly_sort; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_ac_assembly_sort ON public.assembly_components USING btree (assembly_id, sort_order);


--
-- Name: ix_ac_material; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_ac_material ON public.assembly_components USING btree (material_id);


--
-- Name: ix_app_settings_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_app_settings_org_id ON public.app_settings USING btree (org_id);


--
-- Name: ix_assemblies_category_active; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_assemblies_category_active ON public.assemblies USING btree (lower(category)) WHERE (is_active = true);


--
-- Name: ix_assemblies_category_subcategory_active; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_assemblies_category_subcategory_active ON public.assemblies USING btree (lower(category), lower(subcategory)) WHERE (is_active = true);


--
-- Name: ix_assemblies_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_assemblies_org_id ON public.assemblies USING btree (org_id);


--
-- Name: ix_assemblies_subcategory_active; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_assemblies_subcategory_active ON public.assemblies USING btree (lower(subcategory)) WHERE (is_active = true);


--
-- Name: ix_billing_customers_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_billing_customers_org_id ON public.billing_customers USING btree (org_id);


--
-- Name: ix_billing_customers_stripe_customer_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ix_billing_customers_stripe_customer_id ON public.billing_customers USING btree (stripe_customer_id);


--
-- Name: ix_billing_event_logs_stripe_event_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ix_billing_event_logs_stripe_event_id ON public.billing_event_logs USING btree (stripe_event_id);


--
-- Name: ix_billing_event_logs_type; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_billing_event_logs_type ON public.billing_event_logs USING btree (type);


--
-- Name: ix_customers_city_active; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_city_active ON public.customers USING btree (city, is_active);


--
-- Name: ix_customers_company_name; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_company_name ON public.customers USING btree (company_name);


--
-- Name: ix_customers_contact_name; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_contact_name ON public.customers USING btree (contact_name);


--
-- Name: ix_customers_created_at; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_created_at ON public.customers USING btree (created_at);


--
-- Name: ix_customers_lower_email; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_lower_email ON public.customers USING btree (lower((email)::text));


--
-- Name: ix_customers_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_org_id ON public.customers USING btree (org_id);


--
-- Name: ix_customers_user_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_customers_user_id ON public.customers USING btree (user_id);


--
-- Name: ix_dje_items_cat_sub_desc; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_dje_items_cat_sub_desc ON public.dje_items USING btree (category, subcategory, description);


--
-- Name: ix_dje_items_category; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_dje_items_category ON public.dje_items USING btree (category);


--
-- Name: ix_dje_items_lower_description; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_dje_items_lower_description ON public.dje_items USING btree (lower((description)::text));


--
-- Name: ix_dje_items_lower_description_pattern; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_dje_items_lower_description_pattern ON public.dje_items USING btree (lower((description)::text));


--
-- Name: ix_dje_items_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_dje_items_org_id ON public.dje_items USING btree (org_id);


--
-- Name: ix_email_logs_provider_msg_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_email_logs_provider_msg_id ON public.email_logs USING btree (provider_msg_id);


--
-- Name: ix_email_logs_status; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_email_logs_status ON public.email_logs USING btree (status);


--
-- Name: ix_email_logs_to_email; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_email_logs_to_email ON public.email_logs USING btree (to_email);


--
-- Name: ix_estimates_created_at; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_estimates_created_at ON public.estimates USING btree (created_at);


--
-- Name: ix_estimates_customer_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_estimates_customer_id ON public.estimates USING btree (customer_id);


--
-- Name: ix_estimates_name; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_estimates_name ON public.estimates USING btree (lower((name)::text));


--
-- Name: ix_estimates_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_estimates_org_id ON public.estimates USING btree (org_id);


--
-- Name: ix_estimates_user_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_estimates_user_id ON public.estimates USING btree (user_id);


--
-- Name: ix_feedback_org_created_at; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_feedback_org_created_at ON public.feedback USING btree (org_id, created_at);


--
-- Name: ix_feedback_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_feedback_org_id ON public.feedback USING btree (org_id);


--
-- Name: ix_feedback_user_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_feedback_user_id ON public.feedback USING btree (user_id);


--
-- Name: ix_materials_lower_item_description; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_materials_lower_item_description ON public.materials USING btree (lower((item_description)::text));


--
-- Name: ix_materials_lower_item_description_pattern; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_materials_lower_item_description_pattern ON public.materials USING btree (lower((item_description)::text));


--
-- Name: ix_materials_material_type; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_materials_material_type ON public.materials USING btree (material_type);


--
-- Name: ix_materials_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_materials_org_id ON public.materials USING btree (org_id);


--
-- Name: ix_materials_type_active_desc; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_materials_type_active_desc ON public.materials USING btree (material_type, is_active, item_description);


--
-- Name: ix_org_memberships_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_org_memberships_org_id ON public.org_memberships USING btree (org_id);


--
-- Name: ix_org_memberships_user_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_org_memberships_user_id ON public.org_memberships USING btree (user_id);


--
-- Name: ix_subscriptions_current_period_end; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_subscriptions_current_period_end ON public.subscriptions USING btree (current_period_end);


--
-- Name: ix_subscriptions_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_subscriptions_org_id ON public.subscriptions USING btree (org_id);


--
-- Name: ix_subscriptions_price_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_subscriptions_price_id ON public.subscriptions USING btree (price_id);


--
-- Name: ix_subscriptions_product_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_subscriptions_product_id ON public.subscriptions USING btree (product_id);


--
-- Name: ix_subscriptions_status; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_subscriptions_status ON public.subscriptions USING btree (status);


--
-- Name: ix_subscriptions_stripe_subscription_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ix_subscriptions_stripe_subscription_id ON public.subscriptions USING btree (stripe_subscription_id);


--
-- Name: ix_users_org_id; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE INDEX ix_users_org_id ON public.users USING btree (org_id);


--
-- Name: uq_ac_assembly_material_active_idx; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX uq_ac_assembly_material_active_idx ON public.assembly_components USING btree (assembly_id, material_id) WHERE (is_active = true);


--
-- Name: uq_assemblies_lower_name_active_idx; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX uq_assemblies_lower_name_active_idx ON public.assemblies USING btree (lower(name)) WHERE (is_active = true);


--
-- Name: ux_dje_active_norm_per_org; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_active_norm_per_org ON public.dje_items USING btree (org_id, lower(TRIM(BOTH FROM category)), lower(TRIM(BOTH FROM description)), COALESCE(lower(TRIM(BOTH FROM vendor)), ''::text)) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_dje_active_norm_system; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_active_norm_system ON public.dje_items USING btree (lower(TRIM(BOTH FROM category)), lower(TRIM(BOTH FROM description)), COALESCE(lower(TRIM(BOTH FROM vendor)), ''::text)) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_dje_items_cat_desc_vendor_active_true_global; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_cat_desc_vendor_active_true_global ON public.dje_items USING btree (category, description, vendor) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_dje_items_global_norm_key; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_global_norm_key ON public.dje_items USING btree (lower(TRIM(BOTH FROM category)), lower(TRIM(BOTH FROM description)), COALESCE(lower(TRIM(BOTH FROM vendor)), ''::text)) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_dje_items_org_cat_desc_vendor_active_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_org_cat_desc_vendor_active_true ON public.dje_items USING btree (org_id, category, description, vendor) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_dje_items_org_norm_key; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_org_norm_key ON public.dje_items USING btree (org_id, lower(TRIM(BOTH FROM category)), lower(TRIM(BOTH FROM description)), COALESCE(lower(TRIM(BOTH FROM vendor)), ''::text)) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_dje_items_org_seed_key_seeded_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_org_seed_key_seeded_true ON public.dje_items USING btree (org_id, seed_key) WHERE ((is_seed = true) AND (org_id IS NOT NULL));


--
-- Name: ux_dje_items_seed_key_global_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_dje_items_seed_key_global_true ON public.dje_items USING btree (seed_key) WHERE ((is_seed = true) AND (org_id IS NULL));


--
-- Name: ux_materials_active_norm_per_org; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_active_norm_per_org ON public.materials USING btree (org_id, lower(TRIM(BOTH FROM material_type)), lower(TRIM(BOTH FROM item_description))) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_materials_active_norm_system; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_active_norm_system ON public.materials USING btree (lower(TRIM(BOTH FROM material_type)), lower(TRIM(BOTH FROM item_description))) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_materials_global_norm_key; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_global_norm_key ON public.materials USING btree (lower(TRIM(BOTH FROM material_type)), lower(TRIM(BOTH FROM item_description))) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_materials_org_norm_key; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_org_norm_key ON public.materials USING btree (org_id, lower(TRIM(BOTH FROM material_type)), lower(TRIM(BOTH FROM item_description))) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_materials_org_seed_key_seeded_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_org_seed_key_seeded_true ON public.materials USING btree (org_id, seed_key) WHERE ((is_seed = true) AND (org_id IS NOT NULL));


--
-- Name: ux_materials_org_type_desc_active_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_org_type_desc_active_true ON public.materials USING btree (org_id, material_type, item_description) WHERE ((is_active = true) AND (org_id IS NOT NULL));


--
-- Name: ux_materials_seed_key_global_true; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_seed_key_global_true ON public.materials USING btree (seed_key) WHERE ((is_seed = true) AND (org_id IS NULL));


--
-- Name: ux_materials_type_desc_active_true_global; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_materials_type_desc_active_true_global ON public.materials USING btree (material_type, item_description) WHERE ((is_active = true) AND (org_id IS NULL));


--
-- Name: ux_users_lower_email; Type: INDEX; Schema: public; Owner: eesaas_prod_db_user
--

CREATE UNIQUE INDEX ux_users_lower_email ON public.users USING btree (lower((email)::text));


--
-- Name: assemblies assemblies_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assemblies
    ADD CONSTRAINT assemblies_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: assembly_components assembly_components_assembly_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assembly_components
    ADD CONSTRAINT assembly_components_assembly_id_fkey FOREIGN KEY (assembly_id) REFERENCES public.assemblies(id) ON DELETE RESTRICT;


--
-- Name: assembly_components assembly_components_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.assembly_components
    ADD CONSTRAINT assembly_components_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id) ON DELETE RESTRICT;


--
-- Name: billing_customers billing_customers_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.billing_customers
    ADD CONSTRAINT billing_customers_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE RESTRICT;


--
-- Name: email_logs email_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: estimates estimates_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT estimates_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: app_settings fk_app_settings_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT fk_app_settings_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: customers fk_customers_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT fk_customers_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: customers fk_customers_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT fk_customers_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: dje_items fk_dje_items_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.dje_items
    ADD CONSTRAINT fk_dje_items_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: estimates fk_estimates_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT fk_estimates_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: estimates fk_estimates_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT fk_estimates_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: materials fk_materials_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT fk_materials_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: org_memberships fk_org_memberships_org; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT fk_org_memberships_org FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: org_memberships fk_org_memberships_user; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.org_memberships
    ADD CONSTRAINT fk_org_memberships_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users fk_users_org_id_orgs; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_org_id_orgs FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE RESTRICT;


--
-- Name: subscriptions subscriptions_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: eesaas_prod_db_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE RESTRICT;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO eesaas_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO eesaas_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO eesaas_prod_db_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO eesaas_prod_db_user;


--
-- PostgreSQL database dump complete
--

\unrestrict TUkuMkm7IsTf4pQkWCitJxjBgZbYdJyCMsRIqS9MnHIzOT5Je1NsJv5V6g46BBK

