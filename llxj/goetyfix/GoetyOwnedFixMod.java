package llxj.goetyfix;

import net.minecraftforge.fml.common.Mod;

/**
 * Goety Owned Null Guard Fix
 *
 * Fixes the recurring "Ticking entity" NullPointerException caused by
 * Goety's Owned.isAlliedTo (Owned.java:186) forwarding a null entity to
 * vanilla Entity.isAlliedTo(Entity), which dereferences the argument
 * without a null check (Entity.java:2236).
 *
 * The actual fix lives in the mixin: llxj.goetyfix.mixin.OwnedNullGuardMixin
 */
@Mod("goetyfix")
public class GoetyOwnedFixMod {

    public GoetyOwnedFixMod() {
    }
}
