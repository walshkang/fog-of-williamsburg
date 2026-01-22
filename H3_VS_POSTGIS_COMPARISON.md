# H3 Hexagonal Indexing vs PostGIS Polygon Buffer/Merge: Comparison for Fog of War Apps

## Executive Summary

For an MVP fog-of-war exploration app (like Fog of Williamsburg), **PostGIS polygon buffer/merge is recommended** due to simpler implementation, better visual appearance, and sufficient performance for single-user MVP scale. H3 becomes advantageous at scale (thousands of users, millions of activities) but adds complexity that may not be justified for an MVP.

---

## 1. Performance Characteristics

### Storage

**PostGIS Polygon Buffer/Merge:**
- ✅ **Simple storage model**: Single `MULTIPOLYGON` per user per borough
- ✅ **Minimal overhead**: One row per user-borough combination
- ⚠️ **Polygon complexity grows**: As users explore more, the merged polygon becomes more complex (more vertices, more edges)
- ⚠️ **Storage scales with exploration**: More explored area = larger geometry storage

**H3 Hexagonal Indexing:**
- ✅ **Fixed-size storage**: Each hex cell is a compact 64-bit integer key
- ✅ **Predictable growth**: Storage scales linearly with number of hex cells covered
- ✅ **Efficient at scale**: For a borough, you might store ~10K-100K hex IDs (resolution 8-9)
- ✅ **Better compression**: Can use simple integer arrays or bitmaps

**Winner: H3** (especially at scale)

### Query Speed

**PostGIS Polygon Buffer/Merge:**
- ✅ **Simple queries**: `ST_Area(ST_Transform(geometry, 3857))` is fast for single polygons
- ✅ **Direct intersection**: `ST_Intersection(buffer, borough)` is straightforward
- ⚠️ **ST_Union performance**: Merging many buffers can slow down (see optimization strategies below)
- ⚠️ **Complex polygon operations**: As polygon complexity grows, operations slow down
- ⚠️ **Index effectiveness**: GIST indexes help but don't eliminate complexity

**H3 Hexagonal Indexing:**
- ✅ **Lightning-fast lookups**: Converting lat/lon → hex ID is O(1)
- ✅ **Set operations**: Union = `UNION` of hex ID sets (trivial SQL)
- ✅ **Area calculation**: Count hex cells × area per cell (simple multiplication)
- ✅ **No geometric complexity**: All operations are integer-based
- ✅ **Excellent for aggregations**: `GROUP BY hex_id` is extremely fast

**Winner: H3** (especially for frequent updates and scoring)

### Scoring Calculation

**PostGIS Polygon Buffer/Merge:**
```sql
-- Current implementation (fast for MVP)
SELECT ST_Area(ST_Transform(unveiled.geometry, 3857)) / borough.total_area * 100
```
- ✅ **Accurate**: True geometric area calculation
- ✅ **Fast enough for MVP**: Single user, occasional updates
- ⚠️ **Slows with complexity**: Complex polygons take longer to compute area

**H3 Hexagonal Indexing:**
```sql
-- H3 approach (extremely fast)
SELECT COUNT(DISTINCT hex_id) * hex_area / borough.total_area * 100
```
- ✅ **Constant-time calculation**: Count cells, multiply by area
- ✅ **Scales perfectly**: Performance doesn't degrade with exploration
- ⚠️ **Slight approximation**: Hex cells don't perfectly match borough boundaries (edge effects)

**Winner: H3** (for frequent scoring, but PostGIS is fine for MVP)

---

## 2. Visual Appearance

### PostGIS Polygon Buffer/Merge

**Pros:**
- ✅ **Smooth, organic appearance**: Buffered routes create natural-looking revealed areas
- ✅ **Follows actual paths**: 25m/100m buffers around routes look realistic
- ✅ **No visual artifacts**: Continuous polygons without gaps or hex patterns
- ✅ **Professional look**: Matches expectations from apps like Strava heatmaps

**Cons:**
- ⚠️ **Can look "blobby"**: Large merged polygons may have irregular shapes
- ⚠️ **Edge smoothing needed**: May want to apply visual smoothing for fog-of-war effect

**Visual Example**: Think Strava's personal heatmap—smooth gradients following actual routes.

### H3 Hexagonal Indexing

**Pros:**
- ✅ **Distinctive game-like aesthetic**: Hexagonal grid gives a unique "game map" feel
- ✅ **Clear progress visualization**: Easy to see which hex cells are explored
- ✅ **Consistent visual language**: All explored areas have same shape/size

**Cons:**
- ❌ **Hexagonal artifacts**: Visible hex grid pattern may not appeal to all users
- ❌ **Less organic**: Doesn't follow actual route shapes as naturally
- ❌ **Edge effects**: Hex cells don't perfectly align with borough boundaries
- ⚠️ **Coverage gaps**: If using coverage < 1.0, gaps between hexes can look odd

**Visual Example**: Think Civilization VI fog of war—hexagonal grid overlay.

**Winner: PostGIS** (for most users expecting a "real-world" exploration feel)

---

## 3. Implementation Complexity with Supabase/PostGIS

### PostGIS Polygon Buffer/Merge

**Current Implementation Status:**
- ✅ **Already partially implemented**: Your `checkin` endpoint uses `ST_Buffer` + `ST_Union`
- ✅ **Standard PostGIS functions**: Well-documented, widely used
- ✅ **Supabase native support**: PostGIS extension available in Supabase dashboard
- ✅ **Simple data model**: One `MULTIPOLYGON` column per user-borough

**Implementation Steps:**
1. ✅ Enable PostGIS extension (already done)
2. ✅ Create `UnveiledArea` table with `Geometry` column (already done)
3. ✅ Implement buffer/union logic (partially done in `checkin`)
4. ⚠️ **Need to implement**: GPX route processing with 25m buffer
5. ⚠️ **Optimization needed**: For many activities, consider:
   - Using `ST_ClusterDBSCAN` before union (for 1000+ buffers)
   - Increasing `work_mem` for large operations
   - Simplifying geometry periodically

**Complexity: Low-Medium** (mostly done, needs GPX processing)

### H3 Hexagonal Indexing

**Implementation Requirements:**
- ❌ **Extension availability unclear**: H3 extension may not be available on Supabase (needs verification)
- ⚠️ **Additional dependencies**: Need `h3` and `h3_postgis` extensions
- ⚠️ **Data model changes**: Need to store hex IDs instead of/alongside polygons
- ⚠️ **Conversion logic**: Convert points/routes → hex IDs at specific resolution
- ⚠️ **Resolution selection**: Must choose appropriate H3 resolution (likely 8-9 for 25m buffers)

**Implementation Steps:**
1. ❓ Verify H3 extension availability on Supabase (may require support ticket)
2. ⚠️ Install `h3` and `h3_postgis` extensions
3. ⚠️ Add hex ID column(s) to `UnveiledArea` or create new `UnveiledHex` table
4. ⚠️ Implement conversion: `h3_lat_lng_to_cell(lat, lng, resolution)`
5. ⚠️ For routes: Convert each point along route to hex IDs, then union
6. ⚠️ Update scoring logic to count hex cells instead of area
7. ⚠️ Handle edge cases: Hex cells outside borough boundaries

**Complexity: Medium-High** (requires extension verification, new data model, conversion logic)

**Winner: PostGIS** (simpler, already partially implemented, guaranteed Supabase support)

---

## 4. Common Practices in Similar Apps

### Strava Heatmaps
- **Approach**: Raster/tile-based aggregation (not H3, not polygon buffers)
- **Visual**: Smooth gradients following actual routes
- **Scale**: Handles millions of activities globally
- **Takeaway**: Prioritizes visual smoothness over geometric precision

### Wandrer.earth
- **Approach**: Street/node matching (tracks which specific streets/segments explored)
- **Visual**: Discrete street segments, not continuous polygons
- **Scale**: Handles thousands of users
- **Takeaway**: Focuses on street-level precision, not area coverage

### CityStrides
- **Approach**: Similar to Wandrer—street segment tracking
- **Visual**: Street-level completion, not fog-of-war polygons
- **Scale**: 99K+ cities tracked
- **Takeaway**: Street completion is the metric, not area coverage

**Key Insight**: None of these apps use H3 for fog-of-war visualization. They either:
1. Use raster/tile aggregation (Strava)
2. Track discrete features (streets/nodes) rather than continuous areas

**For your use case**: Polygon buffers are actually closer to what users expect than hex grids.

---

## 5. Pros/Cons Summary

### PostGIS Polygon Buffer/Merge

**Pros:**
- ✅ Already partially implemented in your codebase
- ✅ Smooth, organic visual appearance
- ✅ Native Supabase/PostGIS support (no extension uncertainty)
- ✅ Simple data model (one polygon per user-borough)
- ✅ Accurate geometric area calculations
- ✅ Follows actual route shapes naturally

**Cons:**
- ⚠️ ST_Union can slow with many buffers (needs optimization at scale)
- ⚠️ Polygon complexity grows with exploration
- ⚠️ Storage scales with polygon complexity
- ⚠️ Scoring calculation slows with complex polygons

### H3 Hexagonal Indexing

**Pros:**
- ✅ Excellent performance at scale (constant-time operations)
- ✅ Predictable storage growth
- ✅ Fast scoring calculations
- ✅ Unique game-like visual aesthetic
- ✅ Perfect for aggregations and analytics

**Cons:**
- ❌ Extension availability on Supabase uncertain
- ❌ Hexagonal visual artifacts (may not appeal to all users)
- ❌ Less organic appearance (doesn't follow routes naturally)
- ❌ Requires new data model and conversion logic
- ❌ Edge effects at borough boundaries
- ❌ Slight approximation in area calculations

---

## 6. MVP Recommendation

### **Recommendation: PostGIS Polygon Buffer/Merge**

**Rationale:**
1. **Already partially implemented**: Your `checkin` endpoint demonstrates the approach works
2. **Faster to MVP**: No extension verification, no data model changes, minimal new code
3. **Better visual fit**: Smooth polygons match user expectations for exploration apps
4. **Sufficient performance**: For MVP (single user, occasional updates), PostGIS is fast enough
5. **Lower risk**: PostGIS is guaranteed to work on Supabase; H3 may not be available

**Implementation Plan:**
1. Complete GPX processing with 25m buffer (similar to existing 100m checkin buffer)
2. Use `ST_Union` for merging (optimize later if needed with clustering)
3. Monitor performance; if `ST_Union` becomes slow, add `ST_ClusterDBSCAN` optimization
4. Consider H3 migration only if you hit performance issues at scale (1000+ activities per user)

**When to Consider H3:**
- You have 1000+ users with frequent activity uploads
- Scoring calculation becomes slow (>1 second)
- ST_Union operations take >5 seconds
- You want the hexagonal game aesthetic specifically
- H3 extension is confirmed available on Supabase

---

## 7. Hybrid Approach (Future Consideration)

For Phase 2, consider a hybrid:
- **Storage**: Use H3 hex IDs for fast queries and scoring
- **Visualization**: Convert hex IDs → polygons for rendering smooth fog-of-war overlay
- **Best of both**: Fast performance + smooth visuals

This requires more complexity but could be worth it if you scale significantly.

---

## References

- [PostGIS ST_Union Performance Optimization](https://gis.stackexchange.com/questions/294473/how-to-improve-postgis-st-union-performance)
- [H3 with PostGIS](https://blog.rustprooflabs.com/2022/04/postgis-h3-intro)
- [Supabase PostGIS Documentation](https://supabase.com/docs/guides/database/extensions/postgis)
