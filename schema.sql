-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- PROFILES
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    rating_global FLOAT DEFAULT 1200.0 NOT NULL,
    matches_played INT DEFAULT 0 NOT NULL,
    is_banned BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- BOTS
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    active_version_id UUID, -- Updated when a version is activated
    status TEXT CHECK (status IN ('draft', 'active', 'retired')) DEFAULT 'draft' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- BOT VERSIONS
CREATE TABLE bot_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    rules_json JSONB NOT NULL,
    rules_hash TEXT NOT NULL,
    search_depth INT NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Add foreign key constraint to bots for active_version_id
ALTER TABLE bots ADD CONSTRAINT fk_active_version FOREIGN KEY (active_version_id) REFERENCES bot_versions(id) ON DELETE SET NULL;

-- MATCHES
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_a_version UUID NOT NULL REFERENCES bot_versions(id),
    bot_b_version UUID NOT NULL REFERENCES bot_versions(id),
    winner TEXT CHECK (winner IN ('A', 'B', 'draw')),
    termination_reason TEXT CHECK (termination_reason IN ('checkmate', 'timeout', 'illegal', 'draw', 'stalemate', 'insufficient material', 'fifty-move rule', 'threefold repetition')),
    pgn TEXT,
    elo_delta_a FLOAT,
    elo_delta_b FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- MATCH QUEUE
CREATE TABLE match_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_a_version UUID NOT NULL REFERENCES bot_versions(id),
    bot_b_version UUID NOT NULL REFERENCES bot_versions(id),
    status TEXT CHECK (status IN ('queued', 'running', 'completed', 'failed')) DEFAULT 'queued' NOT NULL,
    priority INT DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ELO HISTORY
CREATE TABLE elo_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_version_id UUID NOT NULL REFERENCES bot_versions(id),
    match_id UUID NOT NULL REFERENCES matches(id),
    elo_before FLOAT NOT NULL,
    elo_after FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE elo_history ENABLE ROW LEVEL SECURITY;

-- Policies
-- Profiles: Everyone can read, owners can update
CREATE POLICY "Public profiles are viewable by everyone" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Bots: Everyone can read, owners can manage
CREATE POLICY "Bots are viewable by everyone" ON bots FOR SELECT USING (true);
CREATE POLICY "Users can insert own bots" ON bots FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own bots" ON bots FOR UPDATE USING (auth.uid() = user_id);

-- Bot Versions: Everyone can read, owners can insert
CREATE POLICY "Bot versions are viewable by everyone" ON bot_versions FOR SELECT USING (true);
CREATE POLICY "Users can insert versions for own bots" ON bot_versions FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM bots WHERE id = bot_id AND user_id = auth.uid())
);

-- Matches: Everyone can read
CREATE POLICY "Matches are viewable by everyone" ON matches FOR SELECT USING (true);

-- Match Queue: Read by everyone, workers can update (simplified for now)
CREATE POLICY "Match queue is viewable by everyone" ON match_queue FOR SELECT USING (true);

-- Automated Profile Creation on Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, username)
  VALUES (
    new.id, 
    COALESCE(
      new.raw_user_meta_data->>'full_name', 
      new.raw_user_meta_data->>'user_name', 
      new.email, 
      'user_' || substr(new.id::text, 1, 8)
    )
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
